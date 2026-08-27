# Agent Reference

All agents are defined as Markdown files in the `agents/` directory with CAO YAML frontmatter. Each file contains the agent's system prompt and configuration.

## Agent Hierarchy

```
customer_support_supervisor (supervisor)
├── inventory_specialist (developer)
├── policy_supervisor (supervisor)
│   ├── returns_policy_agent (developer)
│   ├── shipping_policy_agent (developer)
│   └── warranty_policy_agent (developer)
└── refund_specialist (developer)

communication_agent (developer) — called last, no tools
```

## Customer Support Supervisor

**File**: `agents/customer_support_supervisor.md`  
**Role**: `supervisor`  
**Tools**: All 11 MCP tools  

Entry point for all customer support requests. Reads the issue, determines which specialists to invoke, collects their results, and delegates to the communication agent for the final response.

**Key behaviours:**
- Always calls inventory_specialist first to establish context
- Delegates to policy_supervisor for any policy-related sub-question (parallel)
- Only calls refund_specialist for refund/damaged/wrong-item issues
- Never skips communication_agent

## Inventory Specialist

**File**: `agents/inventory_specialist.md`  
**Role**: `developer`  
**Tools**: `get_customer`, `get_customer_tier`, `list_customer_orders`, `get_order`, `get_order_status`, `get_order_items`

Retrieves customer and order data. Returns a structured inventory context for the supervisor.

## Policy Supervisor

**File**: `agents/policy_supervisor.md`  
**Role**: `supervisor`  
**Tools**: None (delegates to policy agents)

Runs all three policy agents in parallel and aggregates their findings. Returns the most relevant policy excerpts for the customer's issue.

## Returns Policy Agent

**File**: `agents/returns_policy_agent.md`  
**Role**: `developer`  
**Tools**: `search_returns_policy` only

Searches the returns policy document and returns relevant excerpts.

## Shipping Policy Agent

**File**: `agents/shipping_policy_agent.md`  
**Role**: `developer`  
**Tools**: `search_shipping_policy` only

Searches the shipping policy document and returns relevant excerpts.

## Warranty Policy Agent

**File**: `agents/warranty_policy_agent.md`  
**Role**: `developer`  
**Tools**: `search_warranty_policy` only

Searches the warranty policy document and returns relevant excerpts.

## Refund Specialist

**File**: `agents/refund_specialist.md`  
**Role**: `developer`  
**Tools**: `calculate_refund_eligibility`, `create_refund_request`

Assesses refund eligibility and creates a refund proposal. Always uses `dry_run=True` unless explicitly authorised. Never approves or rejects — only proposes.

## Communication Agent

**File**: `agents/communication_agent.md`  
**Role**: `developer`  
**Tools**: None

Takes the internal case summary and writes the final customer-facing response. Strict rules: never invents facts, never promises a refund unless eligibility is confirmed, never exposes internal agent names or system details.

## Adding a New Agent

1. Create `agents/new_agent.md` with valid CAO YAML frontmatter
2. Set `role: developer` (or `supervisor` if it coordinates others)
3. Set `allowedTools` to only the tools the agent needs
4. Configure `mcpServers` to point to the SupportMesh MCP server
5. Write the system prompt (the Markdown body below the frontmatter)
6. Reference the agent in the supervisor's prompt if it should be called automatically
