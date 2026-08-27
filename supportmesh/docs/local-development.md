# Local Development Guide

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- Docker (optional, for containerised MCP server)

## Setup

```bash
git clone https://github.com/your-org/supportmesh
cd supportmesh

# Install with uv
make setup
make install-dev

# Or manually
cp .env.example .env
uv sync --all-extras
```

## Running Tests

```bash
# All tests
make test

# Specific file
uv run pytest tests/test_refund.py -v

# With coverage
uv run pytest --cov=mcp --cov=app --cov=workflows --cov-report=term-missing
```

## Running the Demo

```bash
make demo
# Equivalent to:
uv run supportmesh demo
```

This runs the full support workflow locally using data from `data/`.

## Running a Custom Query

```bash
uv run supportmesh ask --customer CUST-001 "Where is my order ORD-1001?"
uv run supportmesh ask -c CUST-001 -o ORD-1001 "I received a damaged item, I need a refund"
```

## Health Check

```bash
make health
# Equivalent to:
uv run supportmesh health
```

## Running the MCP Server Standalone

```bash
make mcp-server
# Equivalent to:
uv run python -m mcp.customer_support_server.server
```

## Using with CAO CLI

Install CAO CLI from [github.com/awslabs/cli-agent-orchestrator](https://github.com/awslabs/cli-agent-orchestrator):

```bash
# Start the MCP server first
uv run python -m mcp.customer_support_server.server &

# Run CAO with the supervisor agent
cao run agents/customer_support_supervisor.md \
  --message "Customer CUST-001 says their order ORD-1001 arrived damaged. Help them."
```

## Environment Variables

All configuration is via environment variables. Copy `.env.example` to `.env` and edit:

```bash
cp .env.example .env
```

Key variables:

| Variable | Default | Notes |
|----------|---------|-------|
| `SUPPORTMESH_ALLOW_MUTATIONS` | `false` | Keep false in dev to prevent accidental refund writes |
| `SUPPORTMESH_DATA_DIR` | `./data` | Points to demo data |
| `SUPPORTMESH_LOG_LEVEL` | `INFO` | Set to `DEBUG` for verbose tool call logs |
| `SUPPORTMESH_DEMO_MODE` | `true` | Enables local operation without AWS |

## Linting and Formatting

```bash
make lint      # ruff check
make format    # ruff format
```

## Adding Sample Data

Edit `data/customers.json` and `data/orders.json`. Data is loaded lazily on first tool call. 

To test with fresh data without restarting:
```python
from mcp.customer_support_server.tools import LocalDataStore, set_data_store
store = LocalDataStore("./data")
set_data_store(store)
```

## Docker

```bash
# Build and start the MCP server container
docker-compose up mcp-server

# The server binds to port 8765 on localhost
```
