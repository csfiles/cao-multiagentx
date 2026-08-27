# Example: Damaged Item Refund Request

## Scenario

Customer CUST-001 (Alice Johnson, Premium tier) received a damaged wireless headset in order ORD-1001 (delivered 2026-08-01, total $289.97).

## CLI Command

```bash
uv run supportmesh ask \
  --customer CUST-001 \
  --order ORD-1001 \
  "I received a damaged item in my order. The wireless headphones arrived with a cracked headband. I'd like a refund."
```

## Workflow

1. **Inventory Specialist** (parallel with Policy Supervisor):
   - `get_customer("CUST-001")` → Premium tier, 60-day return window
   - `get_order("ORD-1001")` → status: delivered, delivered_at: 2026-08-01

2. **Policy Supervisor** (parallel with Inventory Specialist):
   - `search_returns_policy("damaged item refund")` → finds "Damaged item: Item arrived physically damaged... Full refund eligible."
   - `search_shipping_policy(...)` → minimal match
   - `search_warranty_policy(...)` → minimal match

3. **Refund Specialist** (after inventory complete):
   - `calculate_refund_eligibility("ORD-1001", "damaged")` → eligible: true, amount: $289.97
   - `create_refund_request("ORD-1001", "damaged", dry_run=True)` → REF-XXXXXXXX proposed

4. **Communication Agent** → customer-facing response

## Expected Response

```
Dear Alice, thank you for reaching out. We're truly sorry to hear about the issue with
ORD-1001 — receiving a damaged item is never acceptable and we want to make this right.

Your order was delivered and is within your Premium tier 60-day return window.

Great news — your order is eligible for a refund of $289.97. A refund request has been
prepared (reference: REF-XXXXXXXX). Our team will process this within 3-5 business days.

If you have any further questions, please don't hesitate to reach out. We're here to help
and appreciate your patience.
```

## Refund Safety Note

The refund is proposed with `dry_run=True`. To actually process it:
1. A human agent reviews the proposal
2. Sets `SUPPORTMESH_ALLOW_MUTATIONS=true` in a controlled environment
3. Calls `create_refund_request("ORD-1001", "damaged", dry_run=False)`
