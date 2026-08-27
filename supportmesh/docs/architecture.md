# SupportMesh Architecture

## Overview

SupportMesh is a multi-agent customer support system that uses AWS Labs CAO CLI (cli-agent-orchestrator) as the top-level orchestration layer and MCP (Model Context Protocol) servers as the tool/capability layer.

```
Customer Message
       │
       ▼
┌──────────────────────────────┐
│   CAO Support Supervisor     │  (agents/customer_support_supervisor.md)
│   Routes and coordinates     │
└─────────────┬────────────────┘
              │ delegates to
    ┌─────────┼──────────────────────┐
    │         │                      │
    ▼         ▼                      ▼
┌───────┐  ┌─────────────────┐  ┌──────────┐
│ Inven │  │ Policy Superv.  │  │ (queued) │
│ tory  │  │  (parallel sub- │  │          │
│ Spec. │  │   delegation)   │  │          │
└───────┘  └────────┬────────┘  └──────────┘
                    │
        ┌───────────┼───────────┐
        ▼           ▼           ▼
   ┌─────────┐ ┌─────────┐ ┌─────────┐
   │ Returns │ │Shipping │ │Warranty │
   │ Policy  │ │ Policy  │ │ Policy  │
   └─────────┘ └─────────┘ └─────────┘

Then:
┌──────────────────┐
│ Refund Specialist│  (if refund-related)
└────────┬─────────┘
         │
         ▼
┌─────────────────────┐
│ Communication Agent │  (final customer-facing response)
└─────────────────────┘
         │
         ▼
    Customer Response
```

## Layer Separation

| Layer | Technology | Role |
|-------|-----------|------|
| Orchestration | CAO CLI (cli-agent-orchestrator) | Agent routing, session management, LLM calls |
| Tools | MCP Server (FastMCP) | Data access, business logic, refund safety |
| Data | JSON + Markdown files | Demo/local; swappable with DynamoDB |
| CLI | Click + Rich | User-facing interface |
| Config | python-dotenv + env vars | No hard-coded credentials |

## Key Design Decisions

### CAO as Orchestrator

CAO owns all multi-agent coordination. The `customer_support_supervisor` is a CAO supervisor agent that decides which specialists to invoke. The policy specialists run in parallel (via CAO's parallel task execution). No custom orchestration framework is used.

### MCP for Business Tools

All data reads and writes go through the MCP server (`mcp/customer_support_server/server.py`). This means:
- Agents cannot access data directly — they must call tools
- Tool signatures are stable — swapping backends (local → DynamoDB) requires no agent changes
- Tool access is scoped per-agent via `allowedTools` in the CAO profile YAML

### Safety-by-Default

The `create_refund_request` tool is safe by default:
1. `SUPPORTMESH_ALLOW_MUTATIONS=false` (default) — tool always returns a dry-run proposal
2. `SUPPORTMESH_DRY_RUN=true` (default) — additional safety gate
3. Refunds over $500 set `requires_approval=True` — human review required

### Local Demo Mode

The full workflow runs without AWS credentials:
```bash
uv run supportmesh demo
```
Data comes from `data/customers.json`, `data/orders.json`, and `data/policies/*.md`.

## Agent Profiles (CAO YAML)

Each agent is defined in `agents/*.md` with YAML frontmatter:

```yaml
---
name: inventory_specialist
role: developer
provider: bedrock
model: us.anthropic.claude-3-7-sonnet-20250219-v1:0
mcpServers:
  customer_support:
    command: python
    args: ["-m", "mcp.customer_support_server.server"]
allowedTools:
  - get_customer
  - get_customer_tier
  - list_customer_orders
  - get_order
  - get_order_status
  - get_order_items
---
```

The `allowedTools` field restricts each agent to only the tools it needs — a minimal-privilege design.
