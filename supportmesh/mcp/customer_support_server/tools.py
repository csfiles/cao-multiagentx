"""
SupportMesh MCP tool implementations.

The DataStore class provides a pluggable interface for data access. The default
LocalDataStore reads from JSON/Markdown files. Replace it with DynamoDataStore
or BedrockDataStore for AWS-backed deployments without changing the MCP tool
signatures.
"""

from __future__ import annotations

import json
import logging
import os
import re
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path

from .models import (
    Customer,
    Order,
    OrderItem,
    PolicySearchResult,
    RefundEligibility,
    RefundRequest,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Return windows (days) by customer tier
# ---------------------------------------------------------------------------
RETURN_WINDOWS: dict[str, int] = {
    "standard": 30,
    "premium": 60,
    "enterprise": 90,
}

# Refund amount fractions by reason
REFUND_FRACTIONS: dict[str, float] = {
    "damaged": 1.0,
    "wrong_item": 1.0,
    "not_satisfied": 0.5,
    "defective": 1.0,
    "not_received": 1.0,
}


# ---------------------------------------------------------------------------
# Abstract DataStore interface
# ---------------------------------------------------------------------------


class DataStore(ABC):
    """
    Abstract interface for SupportMesh data access.

    Implement this to swap in DynamoDB, Bedrock Knowledge Bases, or any other
    backend without touching the MCP tool signatures.
    """

    @abstractmethod
    async def get_customer(self, customer_id: str) -> Customer | None:
        """Retrieve a customer by ID."""
        ...

    @abstractmethod
    async def list_orders_for_customer(self, customer_id: str) -> list[Order]:
        """List all orders for a customer."""
        ...

    @abstractmethod
    async def get_order(self, order_id: str) -> Order | None:
        """Retrieve an order by ID."""
        ...

    @abstractmethod
    async def search_policy(self, policy_type: str, query: str) -> list[str]:
        """Search a policy document and return matching excerpts."""
        ...

    @abstractmethod
    async def save_refund(self, refund: RefundRequest) -> None:
        """Persist a refund request (only called when mutations are allowed)."""
        ...


# ---------------------------------------------------------------------------
# Local (JSON/Markdown) implementation
# ---------------------------------------------------------------------------


class LocalDataStore(DataStore):
    """
    Reads customers and orders from JSON files, policies from Markdown files.
    Writes refunds to a JSON file when mutations are enabled.

    File layout (relative to data_dir):
        customers.json
        orders.json
        refunds.json
        policies/returns.md
        policies/shipping.md
        policies/warranty.md
    """

    def __init__(self, data_dir: str | Path | None = None) -> None:
        self.data_dir = Path(data_dir or os.getenv("SUPPORTMESH_DATA_DIR", "./data"))
        self._customers: dict[str, Customer] = {}
        self._orders: dict[str, Order] = {}
        self._policy_cache: dict[str, str] = {}
        self._loaded = False

    def _load(self) -> None:
        if self._loaded:
            return
        self._load_customers()
        self._load_orders()
        self._loaded = True

    def _load_customers(self) -> None:
        path = self.data_dir / "customers.json"
        if not path.exists():
            logger.warning("customers.json not found at %s", path)
            return
        with path.open() as f:
            records = json.load(f)
        for rec in records:
            customer = Customer.model_validate(rec)
            self._customers[customer.id] = customer
        logger.debug("Loaded %d customers", len(self._customers))

    def _load_orders(self) -> None:
        path = self.data_dir / "orders.json"
        if not path.exists():
            logger.warning("orders.json not found at %s", path)
            return
        with path.open() as f:
            records = json.load(f)
        for rec in records:
            order = Order.model_validate(rec)
            self._orders[order.id] = order
        logger.debug("Loaded %d orders", len(self._orders))

    def _load_policy(self, policy_type: str) -> str:
        if policy_type in self._policy_cache:
            return self._policy_cache[policy_type]
        path = self.data_dir / "policies" / f"{policy_type}.md"
        if not path.exists():
            logger.warning("Policy file not found: %s", path)
            return ""
        content = path.read_text(encoding="utf-8")
        self._policy_cache[policy_type] = content
        return content

    async def get_customer(self, customer_id: str) -> Customer | None:
        self._load()
        return self._customers.get(customer_id)

    async def list_orders_for_customer(self, customer_id: str) -> list[Order]:
        self._load()
        return [o for o in self._orders.values() if o.customer_id == customer_id]

    async def get_order(self, order_id: str) -> Order | None:
        self._load()
        return self._orders.get(order_id)

    async def search_policy(self, policy_type: str, query: str) -> list[str]:
        """Simple keyword search over the policy Markdown file."""
        content = self._load_policy(policy_type)
        if not content:
            return []

        # Split into paragraphs / sections
        paragraphs = [p.strip() for p in re.split(r"\n\n+", content) if p.strip()]

        # Tokenize query
        keywords = [w.lower() for w in re.split(r"\W+", query) if len(w) > 2]
        if not keywords:
            return paragraphs[:3]

        # Score each paragraph
        scored: list[tuple[float, str]] = []
        for para in paragraphs:
            para_lower = para.lower()
            hits = sum(1 for kw in keywords if kw in para_lower)
            if hits > 0:
                score = hits / len(keywords)
                scored.append((score, para))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [p for _, p in scored[:5]]

    async def save_refund(self, refund: RefundRequest) -> None:
        path = self.data_dir / "refunds.json"
        existing: list[dict] = []
        if path.exists():
            with path.open() as f:
                existing = json.load(f)
        existing.append(refund.model_dump())
        with path.open("w") as f:
            json.dump(existing, f, indent=2)
        logger.info("Refund %s saved to %s", refund.id, path)


# ---------------------------------------------------------------------------
# Module-level default data store
# ---------------------------------------------------------------------------

_default_store: LocalDataStore | None = None


def get_default_store() -> LocalDataStore:
    global _default_store
    if _default_store is None:
        _default_store = LocalDataStore()
    return _default_store


def set_data_store(store: DataStore) -> None:
    """Override the default data store (useful for testing)."""
    global _default_store
    _default_store = store  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# MCP Tool functions
# ---------------------------------------------------------------------------


async def get_customer(customer_id: str) -> dict:
    """
    Retrieve a customer profile by customer ID.

    Args:
        customer_id: Customer identifier (e.g., "CUST-001")

    Returns:
        Customer data dict, or {"error": "not_found", "customer_id": ...}
    """
    store = get_default_store()
    customer = await store.get_customer(customer_id)
    if customer is None:
        logger.info("Customer not found: %s", customer_id)
        return {"error": "not_found", "customer_id": customer_id}
    logger.info("Retrieved customer: %s", customer_id)
    return customer.model_dump()


async def get_customer_tier(customer_id: str) -> dict:
    """
    Get the service tier for a customer.

    Args:
        customer_id: Customer identifier

    Returns:
        {"customer_id": ..., "tier": "standard"|"premium"|"enterprise"} or error
    """
    store = get_default_store()
    customer = await store.get_customer(customer_id)
    if customer is None:
        return {"error": "not_found", "customer_id": customer_id}
    return {"customer_id": customer_id, "tier": customer.tier}


async def list_customer_orders(customer_id: str) -> dict:
    """
    List all orders for a customer.

    Args:
        customer_id: Customer identifier

    Returns:
        {"customer_id": ..., "orders": [...], "count": N}
    """
    store = get_default_store()
    orders = await store.list_orders_for_customer(customer_id)
    logger.info("Found %d orders for customer %s", len(orders), customer_id)
    return {
        "customer_id": customer_id,
        "orders": [o.model_dump() for o in orders],
        "count": len(orders),
    }


async def get_order(order_id: str) -> dict:
    """
    Retrieve full order details by order ID.

    Args:
        order_id: Order identifier (e.g., "ORD-1001")

    Returns:
        Order data dict, or {"error": "not_found", "order_id": ...}
    """
    store = get_default_store()
    order = await store.get_order(order_id)
    if order is None:
        logger.info("Order not found: %s", order_id)
        return {"error": "not_found", "order_id": order_id}
    logger.info("Retrieved order: %s (status=%s)", order_id, order.status)
    return order.model_dump()


async def get_order_status(order_id: str) -> dict:
    """
    Get the current status of an order.

    Args:
        order_id: Order identifier

    Returns:
        {"order_id": ..., "status": ...} or error
    """
    store = get_default_store()
    order = await store.get_order(order_id)
    if order is None:
        return {"error": "not_found", "order_id": order_id}
    return {
        "order_id": order_id,
        "status": order.status,
        "tracking_number": order.tracking_number,
        "shipped_at": order.shipped_at,
        "delivered_at": order.delivered_at,
    }


async def get_order_items(order_id: str) -> dict:
    """
    Get the list of items in an order.

    Args:
        order_id: Order identifier

    Returns:
        {"order_id": ..., "items": [...]} or error
    """
    store = get_default_store()
    order = await store.get_order(order_id)
    if order is None:
        return {"error": "not_found", "order_id": order_id}
    return {
        "order_id": order_id,
        "items": [item.model_dump() for item in order.items],
        "item_count": len(order.items),
    }


async def calculate_refund_eligibility(order_id: str, reason: str) -> dict:
    """
    Calculate whether a refund is eligible for an order.

    Eligibility rules:
    - Order must exist and be in "delivered" status
    - Days since delivery must be within the tier's return window
    - Reason determines refund amount fraction

    Args:
        order_id: Order identifier
        reason: Reason for refund (e.g., "damaged", "wrong_item", "not_satisfied")

    Returns:
        RefundEligibility data dict
    """
    store = get_default_store()
    order = await store.get_order(order_id)

    if order is None:
        result = RefundEligibility(
            order_id=order_id,
            reason=reason,
            eligible=False,
            reason_text=f"Order {order_id} was not found in the system.",
            eligible_amount=0.0,
            requires_approval=False,
            confidence=1.0,
        )
        return result.model_dump()

    # Must be delivered to be eligible for a refund
    if order.status != "delivered":
        result = RefundEligibility(
            order_id=order_id,
            reason=reason,
            eligible=False,
            reason_text=(
                f"Order {order_id} is not eligible for a refund because its status "
                f"is '{order.status}', not 'delivered'."
            ),
            eligible_amount=0.0,
            requires_approval=False,
            confidence=1.0,
        )
        return result.model_dump()

    # Check delivery date
    if order.delivered_at is None:
        result = RefundEligibility(
            order_id=order_id,
            reason=reason,
            eligible=False,
            reason_text="Order has no delivery date recorded — cannot assess eligibility.",
            eligible_amount=0.0,
            requires_approval=False,
            confidence=0.5,
        )
        return result.model_dump()

    # Get customer tier
    customer = await store.get_customer(order.customer_id)
    tier = customer.tier if customer else "standard"
    window_days = RETURN_WINDOWS.get(tier, 30)

    # Calculate days since delivery
    delivered_dt = datetime.fromisoformat(order.delivered_at.replace("Z", "+00:00"))
    now = datetime.now(tz=timezone.utc)
    days_since = (now - delivered_dt).days

    if days_since > window_days:
        result = RefundEligibility(
            order_id=order_id,
            reason=reason,
            eligible=False,
            reason_text=(
                f"Return window expired. {tier.capitalize()} customers have {window_days} days "
                f"to return; {days_since} days have passed since delivery."
            ),
            eligible_amount=0.0,
            requires_approval=False,
            confidence=1.0,
        )
        return result.model_dump()

    # Calculate eligible amount
    fraction = REFUND_FRACTIONS.get(reason.lower(), 0.5)
    eligible_amount = round(order.total * fraction, 2)
    requires_approval = eligible_amount > 500.0

    result = RefundEligibility(
        order_id=order_id,
        reason=reason,
        eligible=True,
        reason_text=(
            f"Order is eligible for a {int(fraction * 100)}% refund (${eligible_amount:.2f}). "
            f"Delivered {days_since} days ago; {tier} tier window is {window_days} days."
        ),
        eligible_amount=eligible_amount,
        requires_approval=requires_approval,
        confidence=1.0,
    )
    logger.info(
        "Refund eligibility for %s: eligible=%s amount=%.2f",
        order_id,
        result.eligible,
        result.eligible_amount,
    )
    return result.model_dump()


async def create_refund_request(order_id: str, reason: str, dry_run: bool = True) -> dict:
    """
    Create a refund request for an order.

    SAFETY: This operation is safe by default. It will NOT write to storage unless
    SUPPORTMESH_ALLOW_MUTATIONS=true AND dry_run=False.

    Args:
        order_id: Order identifier
        reason: Reason for the refund
        dry_run: If True (default), return a proposal without writing. Never set
                 to False without explicit authorization.

    Returns:
        RefundRequest data dict (with dry_run=True for proposals)
    """
    allow_mutations = os.getenv("SUPPORTMESH_ALLOW_MUTATIONS", "false").lower() == "true"
    force_dry_run = os.getenv("SUPPORTMESH_DRY_RUN", "true").lower() == "true"

    # Safety gate: if mutations are not allowed, or dry_run is globally forced
    effective_dry_run = dry_run or not allow_mutations or force_dry_run

    if not effective_dry_run and not allow_mutations:
        logger.warning(
            "create_refund_request called with dry_run=False but SUPPORTMESH_ALLOW_MUTATIONS=false; "
            "reverting to dry-run."
        )
        effective_dry_run = True

    # Calculate the refund amount
    eligibility_dict = await calculate_refund_eligibility(order_id, reason)
    eligible_amount = eligibility_dict.get("eligible_amount", 0.0)

    refund = RefundRequest(
        id=f"REF-{uuid.uuid4().hex[:8].upper()}",
        order_id=order_id,
        reason=reason,
        amount=eligible_amount,
        status="proposed" if effective_dry_run else "pending",
        created_at=datetime.now(tz=timezone.utc).isoformat(),
        dry_run=effective_dry_run,
    )

    if not effective_dry_run:
        store = get_default_store()
        await store.save_refund(refund)
        logger.info("LIVE refund request created: %s for order %s", refund.id, order_id)
    else:
        logger.info(
            "DRY-RUN refund proposal: %s for order %s (amount=%.2f)",
            refund.id,
            order_id,
            refund.amount,
        )

    return refund.model_dump()


async def search_returns_policy(query: str) -> dict:
    """
    Search the returns policy document for information relevant to the query.

    Args:
        query: Natural language search query (e.g., "return window electronics")

    Returns:
        PolicySearchResult data dict
    """
    store = get_default_store()
    matches = await store.search_policy("returns", query)
    confidence = min(1.0, len(matches) * 0.25) if matches else 0.0
    result = PolicySearchResult(
        query=query,
        policy_type="returns",
        matches=matches,
        confidence=confidence,
    )
    logger.info("Returns policy search '%s' → %d matches", query, len(matches))
    return result.model_dump()


async def search_shipping_policy(query: str) -> dict:
    """
    Search the shipping policy document for information relevant to the query.

    Args:
        query: Natural language search query (e.g., "express delivery time")

    Returns:
        PolicySearchResult data dict
    """
    store = get_default_store()
    matches = await store.search_policy("shipping", query)
    confidence = min(1.0, len(matches) * 0.25) if matches else 0.0
    result = PolicySearchResult(
        query=query,
        policy_type="shipping",
        matches=matches,
        confidence=confidence,
    )
    logger.info("Shipping policy search '%s' → %d matches", query, len(matches))
    return result.model_dump()


async def search_warranty_policy(query: str) -> dict:
    """
    Search the warranty policy document for information relevant to the query.

    Args:
        query: Natural language search query (e.g., "electronics warranty period")

    Returns:
        PolicySearchResult data dict
    """
    store = get_default_store()
    matches = await store.search_policy("warranty", query)
    confidence = min(1.0, len(matches) * 0.25) if matches else 0.0
    result = PolicySearchResult(
        query=query,
        policy_type="warranty",
        matches=matches,
        confidence=confidence,
    )
    logger.info("Warranty policy search '%s' → %d matches", query, len(matches))
    return result.model_dump()
