# SupportMesh

Multi-agent customer support system using [AWS Labs CAO CLI](https://github.com/awslabs/cli-agent-orchestrator) for orchestration and [MCP](https://modelcontextprotocol.io/) for business tools.

```
Customer → CAO Supervisor → [Inventory + Policy Agents (parallel)] → Refund Specialist → Communication Agent → Customer
```

## Features

- **CAO-native orchestration** — each agent is a `.md` file with YAML frontmatter; CAO handles routing, session management, and LLM calls
- **MCP tool layer** — all data access goes through a FastMCP server; agents cannot touch data directly
- **Parallel policy agents** — returns, shipping, and warranty agents run concurrently via CAO's parallel task execution
- **Safety-by-default** — refund operations are dry-run only unless `SUPPORTMESH_ALLOW_MUTATIONS=true`
- **Local demo mode** — runs fully offline using JSON + Markdown files; no AWS credentials required
- **Pluggable data backend** — swap `LocalDataStore` for `DynamoDataStore` without changing agent interfaces

## Quick Start

```bash
git clone https://github.com/your-org/supportmesh
cd supportmesh

# Install
make setup && make install

# Health check
make health

# Run the demo
make demo
```

## Usage

```bash
# Order status
uv run supportmesh ask --customer CUST-001 "Where is my order ORD-1001?"

# Damaged item refund
uv run supportmesh ask -c CUST-001 -o ORD-1001 "I received a damaged item, I need a refund"

# Policy question
uv run supportmesh ask -c CUST-002 "What is your return policy?"

# JSON output
uv run supportmesh ask --customer CUST-001 --json-output "Order status ORD-1001"

# Start MCP server standalone
uv run supportmesh mcp-server
```

## Architecture

```
agents/                  CAO agent profiles (YAML + system prompt)
├── customer_support_supervisor.md
├── inventory_specialist.md
├── policy_supervisor.md
├── returns_policy_agent.md
├── shipping_policy_agent.md
├── warranty_policy_agent.md
├── refund_specialist.md
└── communication_agent.md

mcp/customer_support_server/   FastMCP server
├── models.py            Pydantic data models
├── tools.py             Tool implementations + DataStore
└── server.py            FastMCP app + tool registrations

app/                     CLI application
├── cli.py               Click commands
├── config.py            Env-var configuration
├── models.py            Workflow-level models
└── formatting.py        Rich terminal output

workflows/
└── support_workflow.py  Local workflow (no CAO dependency for demo)

data/
├── customers.json
├── orders.json
├── refunds.json          (initially empty; written if mutations enabled)
└── policies/
    ├── returns.md
    ├── shipping.md
    └── warranty.md
```

## Agent Flow

| Step | Agents | Parallel? |
|------|--------|-----------|
| 1 | Inventory Specialist | Parallel with step 2 |
| 2 | Policy Supervisor → [Returns, Shipping, Warranty] | Parallel within supervisor |
| 3 | Refund Specialist (if refund issue) | Sequential after step 1 |
| 4 | Communication Agent | Sequential (needs all results) |

## Configuration

Copy `.env.example` to `.env` and configure:

| Variable | Default | Description |
|----------|---------|-------------|
| `SUPPORTMESH_ALLOW_MUTATIONS` | `false` | Enable refund writes |
| `SUPPORTMESH_DRY_RUN` | `true` | Force dry-run globally |
| `SUPPORTMESH_DATA_DIR` | `./data` | Local data directory |
| `SUPPORTMESH_MODEL` | claude-3-7-sonnet | Bedrock model ID |
| `SUPPORTMESH_LOG_LEVEL` | `INFO` | Log verbosity |
| `AWS_REGION` | `us-east-1` | AWS region (CAO mode only) |
| `AWS_PROFILE` | — | AWS profile (optional) |

## Using with CAO

Install CAO CLI:
```bash
pip install cli-agent-orchestrator
# or build from source:
git clone https://github.com/awslabs/cli-agent-orchestrator
cd cli-agent-orchestrator && pip install .
```

Start the MCP server, then run CAO:
```bash
uv run python -m mcp.customer_support_server.server &

cao run agents/customer_support_supervisor.md \
  --message "Customer CUST-001 reports a damaged item in order ORD-1001."
```

## Development

```bash
make install-dev  # install with dev dependencies
make test         # run pytest
make lint         # ruff check
make format       # ruff format
```

## Sample Data

| ID | Name | Tier | Orders |
|----|------|------|--------|
| CUST-001 | Alice Johnson | Premium | ORD-1001 (delivered), ORD-1002 (shipped) |
| CUST-002 | Bob Martinez | Standard | ORD-1003 (delivered) |
| CUST-003 | Priya Sharma | Enterprise | ORD-1004 (delivered, $1456) |

## Safety

- `create_refund_request` always returns `dry_run=True` unless `SUPPORTMESH_ALLOW_MUTATIONS=true`
- Refunds over $500 set `requires_approval=True`
- No credentials are stored in source code or data files
- See [SECURITY.md](SECURITY.md) for the full security model

## License

MIT — see [LICENSE](LICENSE).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).
