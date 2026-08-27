# CAO CLI — CLI Agent Orchestrator

A Python reimplementation of [AWS Labs CLI Agent Orchestrator](https://github.com/awslabs/cli-agent-orchestrator).

Multi-agent orchestration using Markdown agent profiles and MCP (Model Context Protocol) tools.

## Features

- **Markdown agent profiles** — define agents with YAML frontmatter (`name`, `provider`, `model`, `role`, `mcpServers`)
- **`assign`** — non-blocking agent launch, caller gets `terminal_id` and continues
- **`handoff`** — blocking agent execution, caller waits for result
- **`send_message`** — async message delivery to terminals or session inbox
- **Provider abstraction** — `mock` (local demo, no credentials needed), `claude_code` (subprocess)
- **`cao-mcp-server`** — MCP server exposing all orchestration tools to agents
- **`cao-server`** — optional REST API for session management

## Quick Start

```bash
# Install
uv pip install -e ".[dev]"

# List agents in current directory
cao agents

# Run an agent with mock provider
cao run agents/inventory_specialist.md --input "Check order ORD-1001" --provider mock

# Run a supervisor (uses agent's own provider setting)
cao launch customer_support_supervisor --input "My order arrived damaged"
```

## Agent Profile Format

```markdown
---
name: inventory-specialist
description: Looks up order and inventory data
provider: claude_code
model: claude-sonnet-4-5
role: inventory
mcpServers:
  cao-mcp-server:
    type: stdio
    command: cao-mcp-server
    args: []
---

You are an inventory specialist. You look up order status, item details,
and shipping information. Use the handoff tool to escalate to refund
specialists when needed.
```

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `CAO_AGENT_PATHS` | `agents:.` | Colon-separated directories to search for `.md` profiles |
| `CAO_LOG_LEVEL` | `WARNING` | Log verbosity (`DEBUG`/`INFO`/`WARNING`/`ERROR`) |
| `CAO_CLAUDE_BINARY` | `claude` | Path to the `claude` CLI binary |
| `CAO_HOST` | `127.0.0.1` | Host for `cao-server` |
| `CAO_PORT` | `8765` | Port for `cao-server` |

## MCP Tools

When `cao-mcp-server` is declared in an agent's `mcpServers`, the agent gets access to:

- **`assign(agent_name, message)`** — launch agent in background, returns `terminal_id`
- **`handoff(agent_name, message)`** — blocking execution, returns full result
- **`send_message(message, receiver_id)`** — deliver message to terminal or session inbox
- **`list_agents()`** — discover available agent profiles

## Development

```bash
make install   # install with dev dependencies
make test      # run tests
make lint      # ruff lint
make check     # lint + test
make demo      # run mock demo
```

## Providers

| Provider | Description |
|---|---|
| `mock` | In-process mock responses, no credentials, role-aware |
| `claude_code` | Runs `claude --print` as subprocess |

## License

Apache 2.0
