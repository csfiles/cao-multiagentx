"""Mock provider for testing and local demos without LLM credentials."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from cao.providers.base import BaseProvider, ProviderConfig, ProviderResponse

logger = logging.getLogger(__name__)


class MockProvider(BaseProvider):
    """Simulates agent responses for local development and testing."""

    @classmethod
    def name(cls) -> str:
        return "mock"

    async def run_turn(
        self,
        message: str,
        config: ProviderConfig,
        history: list[dict[str, str]] | None = None,
    ) -> ProviderResponse:
        await asyncio.sleep(0.05)  # simulate network latency

        role_responses = _build_role_response(config.system_prompt, message)
        logger.debug("mock provider responding to: %.60s", message)

        return ProviderResponse(
            content=role_responses,
            tool_calls=[],
            tokens_used=len(role_responses) // 4,
            provider="mock",
            model=config.model,
        )


def _build_role_response(system_prompt: str, message: str) -> str:
    """Generate a context-appropriate mock response based on agent role keywords."""
    sp = system_prompt.lower()
    msg = message.lower()

    if "inventory" in sp or "order" in sp:
        return _inventory_response(message)
    if "returns" in sp and "policy" in sp:
        return _returns_policy_response()
    if "shipping" in sp and "policy" in sp:
        return _shipping_policy_response()
    if "warranty" in sp and "policy" in sp:
        return _warranty_policy_response()
    if "refund" in sp:
        return _refund_response(message)
    if "communication" in sp or "customer-facing" in sp or "response" in sp:
        return _communication_response(message)
    if "supervisor" in sp or "orchestrat" in sp:
        return _supervisor_response(message)
    return f"[Mock agent processed: {message[:80]}]"


def _inventory_response(message: str) -> str:
    order_id = "ORD-1001"
    for word in message.split():
        if word.upper().startswith("ORD-"):
            order_id = word.upper().rstrip(".,?!")
            break

    return (
        f"**Inventory findings for {order_id}:**\n"
        f"- Order status: Shipped (2025-08-22)\n"
        f"- Customer: Alice Johnson (Premium tier)\n"
        f"- Items: 1x Wireless Headphones (SKU: AUDIO-WH-200)\n"
        f"- Tracking: 1Z999AA10123456784 — In transit, estimated delivery Aug 27\n"
        f"- Order total: $89.99 USD"
    )


def _returns_policy_response() -> str:
    return (
        "**Returns Policy findings:**\n"
        "- Standard customers: 30-day return window from delivery\n"
        "- Premium customers: 60-day return window\n"
        "- Enterprise customers: 90-day return window\n"
        "- Damaged/defective items eligible for full refund within window\n"
        "- Items must be in original packaging for non-defective returns\n"
        "- Confidence: HIGH"
    )


def _shipping_policy_response() -> str:
    return (
        "**Shipping Policy findings:**\n"
        "- Standard shipping: 5–7 business days, free over $50\n"
        "- Express shipping: 2–3 business days, $9.99\n"
        "- Overnight: next business day, $24.99\n"
        "- Damaged-in-transit claims: contact support within 48 hours of delivery\n"
        "- Confidence: HIGH"
    )


def _warranty_policy_response() -> str:
    return (
        "**Warranty Policy findings:**\n"
        "- Standard products: 90-day limited warranty\n"
        "- Electronics: 1-year manufacturer warranty\n"
        "- Premium members: extended 2-year warranty on electronics\n"
        "- Physical damage not covered under standard warranty\n"
        "- Confidence: HIGH"
    )


def _refund_response(message: str) -> str:
    return (
        "**Refund eligibility assessment:**\n"
        "- Order is within refund window for customer tier\n"
        "- Reason 'damaged' qualifies for 100% refund\n"
        "- Eligible amount: $89.99\n"
        "- Proposed action: APPROVE REFUND (requires confirmation)\n"
        "- Requires explicit customer confirmation before processing\n"
        "- [DRY RUN — no actual refund issued]\n"
        "- Confidence: 0.92"
    )


def _communication_response(message: str) -> str:
    return (
        "Dear valued customer,\n\n"
        "Thank you for reaching out to us. We've reviewed your case and I'm "
        "pleased to let you know that based on our investigation, your order "
        "qualifies for the resolution you requested.\n\n"
        "Our team has reviewed the details and will process your request "
        "within 2–3 business days. You will receive a confirmation email "
        "at the address on file.\n\n"
        "If you have any further questions, please don't hesitate to contact us.\n\n"
        "Best regards,\n"
        "Customer Support Team"
    )


def _supervisor_response(message: str) -> str:
    return (
        "Analyzed customer request. Routing to specialist agents:\n"
        "- Dispatching Inventory Specialist (async)\n"
        "- Dispatching Policy Supervisor (async)\n"
        "- Will dispatch Refund Specialist after inventory confirmed\n"
        "Awaiting specialist results..."
    )
