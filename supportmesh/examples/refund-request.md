# Example: Direct Refund Request

## Scenario

Customer CUST-003 (Priya Sharma, Enterprise tier) received the wrong monitors in order ORD-1004 (delivered 2026-07-18, total $1456.00). High-value order — requires manager approval.

## CLI Command

```bash
uv run supportmesh ask \
  --customer CUST-003 \
  --order ORD-1004 \
  "I ordered 27-inch 4K monitors but received 24-inch 1080p monitors instead. This is wrong."
```

## Workflow

1. **Inventory Specialist**:
   - `get_customer("CUST-003")` → Enterprise tier (90-day window)
   - `get_order("ORD-1004")` → delivered, total $1456.00

2. **Policy Supervisor** (parallel):
   - Returns policy: "Wrong item: Customer received an item different from what was ordered. Full refund or exchange eligible."

3. **Refund Specialist**:
   - `calculate_refund_eligibility("ORD-1004", "wrong_item")` → eligible: true, amount: $1456.00, **requires_approval: true** (>$500)
   - `create_refund_request("ORD-1004", "wrong_item", dry_run=True)` → proposed

## High-Value Approval Flow

Because `requires_approval=True`:
- The workflow sets `follow_up_required=True`
- The communication agent tells the customer a manager will review

## Expected Response

```
Dear Priya, thank you for contacting us regarding ORD-1004. We've reviewed your refund
request and have the following update for you.

Your order was delivered and is within your Enterprise tier 90-day return window.

Your order appears to be eligible for a full refund of $1456.00 due to receiving the wrong
item. A refund request has been prepared (reference: REF-XXXXXXXX). Because this is a
high-value refund, our team will contact you within 1 business day to complete the process.

If you have any further questions, please don't hesitate to reach out.
```
