"""Pydantic models for the SupportMesh MCP customer-support server."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class Address(BaseModel):
    """Customer mailing address."""

    street: str
    city: str
    state: str
    zip: str
    country: str


class Customer(BaseModel):
    """Customer profile."""

    id: str
    name: str
    email: str
    tier: Literal["standard", "premium", "enterprise"]
    since: str  # ISO date string
    address: Address


class OrderItem(BaseModel):
    """A single line item within an order."""

    id: str
    name: str
    sku: str
    quantity: int
    price: float
    category: str


class Order(BaseModel):
    """Customer order."""

    id: str
    customer_id: str
    status: Literal[
        "pending", "processing", "shipped", "delivered", "cancelled", "returned"
    ]
    items: list[OrderItem]
    total: float
    currency: str = "USD"
    created_at: str  # ISO datetime string
    shipped_at: str | None = None
    delivered_at: str | None = None
    tracking_number: str | None = None


class RefundRequest(BaseModel):
    """A refund request — may be a dry-run proposal or a real request."""

    id: str
    order_id: str
    reason: str
    amount: float
    status: Literal["proposed", "pending", "approved", "rejected", "completed"]
    created_at: str  # ISO datetime string
    dry_run: bool = True

    @property
    def is_live(self) -> bool:
        """True if this is a real refund request (not a dry-run)."""
        return not self.dry_run


class PolicySearchResult(BaseModel):
    """Result of a policy document search."""

    query: str
    policy_type: Literal["returns", "shipping", "warranty"]
    matches: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)


class RefundEligibility(BaseModel):
    """Refund eligibility assessment for an order."""

    order_id: str
    reason: str
    eligible: bool
    reason_text: str
    eligible_amount: float
    requires_approval: bool = False
    confidence: float = Field(ge=0.0, le=1.0, default=1.0)
