# Example: Basic Order Status Query

## Scenario

Customer CUST-001 (Alice Johnson, Premium tier) wants to know the status of order ORD-1002.

## CLI Command

```bash
uv run supportmesh ask --customer CUST-001 --order ORD-1002 "Where is my order?"
```

## What Happens

1. **Inventory Specialist** calls `get_order("ORD-1002")` → status: `shipped`, tracking: `1Z999AA10987654321`
2. **Policy Supervisor** searches all three policies for "order status" → minimal matches (not a policy question)
3. **Communication Agent** formats a tracking response

## Expected Response

```
Dear Alice, thank you for checking in about ORD-1002. Here's the latest status on your order.

Your order has been shipped. Tracking: 1Z999AA10987654321.

If you have any further questions, please don't hesitate to reach out.
```

## JSON Output

```bash
uv run supportmesh ask --customer CUST-001 --order ORD-1002 --json-output "Order status?"
```

```json
{
  "request": { "customer_id": "CUST-001", "issue_type": "order_status", ... },
  "case_summary": {
    "order_data": { "id": "ORD-1002", "status": "shipped", "tracking_number": "..." },
    "refund_eligibility": null
  },
  "customer_message": "Dear Alice...",
  "resolved": true,
  "follow_up_required": false
}
```
