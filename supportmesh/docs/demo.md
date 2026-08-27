# Running the Demo

## Quick Start

```bash
make setup && make install
make demo
```

This runs a pre-configured scenario: customer CUST-001 reports a damaged item in order ORD-1001.

## Manual Queries

```bash
# Order status
uv run supportmesh ask --customer CUST-001 "Where is my order ORD-1001?"

# Refund request
uv run supportmesh ask -c CUST-001 -o ORD-1001 "I received a damaged item, I need a refund"

# Policy question
uv run supportmesh ask -c CUST-002 "What is your return policy for electronics?"

# Wrong item
uv run supportmesh ask -c CUST-003 -o ORD-1004 "I received the wrong monitors"

# JSON output (for scripting)
uv run supportmesh ask --customer CUST-001 --json-output "Check order status ORD-1001"
```

## Sample Data

| Customer | Tier | Notable Orders |
|----------|------|----------------|
| CUST-001 | Premium | ORD-1001 (delivered), ORD-1002 (shipped) |
| CUST-002 | Standard | ORD-1003 (delivered) |
| CUST-003 | Enterprise | ORD-1004 (delivered, high value $1456) |

### Interesting scenarios to try

- `CUST-001 / ORD-1001 / damaged` → Eligible for $289.97 refund (premium, 60-day window)
- `CUST-002 / ORD-1003 / not_satisfied` → 50% refund ($52.49)
- `CUST-003 / ORD-1004 / damaged` → Eligible but requires approval (>$500)
- `CUST-001 / ORD-1002` → Not eligible (order not yet delivered)

## Health Check

```bash
uv run supportmesh health
```

Verifies data files are loaded and policies are readable.

## Running with CAO (full multi-agent mode)

With CAO CLI installed and AWS credentials configured:

```bash
# Start MCP server
uv run python -m mcp.customer_support_server.server &

# Run with CAO
cao run agents/customer_support_supervisor.md \
  --message "Customer CUST-001 says order ORD-1001 arrived damaged. They want a refund."
```

The CAO supervisor will invoke inventory_specialist and policy_supervisor in parallel, then pass results to refund_specialist and finally communication_agent.
