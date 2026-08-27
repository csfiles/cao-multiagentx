# MCP Server Reference

## Overview

The SupportMesh MCP server provides customer support tools to CAO agents. It is built with FastMCP and exposes 11 tools across four categories.

## Running the Server

```bash
# Via CLI
uv run supportmesh mcp-server

# Via Python module (for CAO agent mcpServers config)
python -m mcp.customer_support_server.server

# Via Docker
docker-compose up mcp-server
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `SUPPORTMESH_DATA_DIR` | `./data` | Directory containing JSON and policy files |
| `SUPPORTMESH_ALLOW_MUTATIONS` | `false` | Enable real writes (refund creation) |
| `SUPPORTMESH_DRY_RUN` | `true` | Force dry-run even if mutations allowed |
| `SUPPORTMESH_LOG_LEVEL` | `INFO` | Logging verbosity |

## Tool Reference

### Customer Tools

#### `get_customer(customer_id: str) -> dict`

Returns full customer profile including tier and address.

```json
{
  "id": "CUST-001",
  "name": "Alice Johnson",
  "email": "alice.johnson@example.com",
  "tier": "premium",
  "since": "2021-03-15",
  "address": { "street": "...", "city": "Seattle", ... }
}
```

#### `get_customer_tier(customer_id: str) -> dict`

Returns only the customer tier (lightweight).

```json
{ "customer_id": "CUST-001", "tier": "premium" }
```

#### `list_customer_orders(customer_id: str) -> dict`

Returns all orders for a customer.

```json
{ "customer_id": "CUST-001", "count": 2, "orders": [...] }
```

### Order Tools

#### `get_order(order_id: str) -> dict`

Returns full order details including items, totals, and shipping info.

#### `get_order_status(order_id: str) -> dict`

Returns order status and tracking — lighter than `get_order`.

```json
{
  "order_id": "ORD-1001",
  "status": "delivered",
  "tracking_number": "1Z999AA10123456784",
  "shipped_at": "2026-07-29T14:30:00Z",
  "delivered_at": "2026-08-01T11:00:00Z"
}
```

#### `get_order_items(order_id: str) -> dict`

Returns the line items in an order.

### Refund Tools

#### `calculate_refund_eligibility(order_id: str, reason: str) -> dict`

Calculates whether a refund is eligible and for how much.

```json
{
  "order_id": "ORD-1001",
  "reason": "damaged",
  "eligible": true,
  "reason_text": "Order is eligible for a 100% refund ($289.97). Delivered 24 days ago; premium tier window is 60 days.",
  "eligible_amount": 289.97,
  "requires_approval": false,
  "confidence": 1.0
}
```

**Eligibility rules:**
- Order status must be `delivered`
- Days since delivery must be within the tier window (standard=30, premium=60, enterprise=90)
- Reason determines fraction: `damaged`/`wrong_item`/`defective`/`not_received` = 100%, `not_satisfied` = 50%

#### `create_refund_request(order_id: str, reason: str, dry_run: bool = True) -> dict`

Creates a refund request. **Safe by default** — always dry-run unless mutations are enabled.

```json
{
  "id": "REF-A1B2C3D4",
  "order_id": "ORD-1001",
  "reason": "damaged",
  "amount": 289.97,
  "status": "proposed",
  "dry_run": true,
  "created_at": "2026-08-25T12:00:00+00:00"
}
```

### Policy Tools

#### `search_returns_policy(query: str) -> dict`
#### `search_shipping_policy(query: str) -> dict`
#### `search_warranty_policy(query: str) -> dict`

Search policy Markdown documents. Returns matching paragraphs and a confidence score.

```json
{
  "query": "return window premium customers",
  "policy_type": "returns",
  "matches": [
    "- **Premium tier**: 60 days from delivery date",
    "All return windows are calculated from the confirmed delivery date..."
  ],
  "confidence": 0.5
}
```

## Extending the Server

To add a new tool:

1. Add the tool function to `mcp/customer_support_server/tools.py`
2. Register it in `server.py` with `@mcp.tool()`
3. Add it to the relevant agent's `allowedTools` list in `agents/*.md`
4. Write a test in `tests/test_mcp_server.py`

To swap the data backend (e.g., DynamoDB):

1. Implement `DataStore` from `tools.py`
2. Call `set_data_store(YourDynamoStore())` at startup
