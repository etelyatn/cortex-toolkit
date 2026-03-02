---
name: cortex-bp-create
description: Use when creating new Blueprints with variables, functions, or components from a spec or description
---

# Blueprint Create

Creates Blueprint assets using the `create_blueprint_graph` composite tool via the Blueprint Developer agent.

## Steps

### 1. Launch Blueprint Developer Agent

<!-- Turn budget: CREATE tier (max_turns=25) — design + execute + verify pattern -->
Use the Task tool with `subagent_type: "cortex-toolkit:blueprint-developer"` and `max_turns: 25` to delegate Blueprint creation.

Pass the full user specification including:
- Blueprint type (Actor, ActorComponent, FunctionLibrary, Interface, etc.)
- Name and desired path
- Variables (name, type, default value, category, exposed status)
- Functions (name, inputs, outputs)
- Graph nodes and connections (BeginPlay events, function calls, branches, etc.)
- Pin values for node configuration

### 2. Agent Workflow (runs in background)

The Blueprint Developer agent will:
1. Read `.cortex/domains/blueprints.md` for node class names and pin conventions
2. Investigate existing Blueprints to avoid name collisions
3. **Use `create_blueprint_graph` composite tool** — single call creates the entire Blueprint
4. Review warnings from auto_layout and compilation
5. Report final result with asset path and stats

**IMPORTANT:** The agent MUST use `create_blueprint_graph` for new Blueprint creation. Individual tools (`create_blueprint`, `add_blueprint_variable`, `graph_add_node`) are PROHIBITED for new Blueprint creation.

### 3. Review Agent Results

The agent returns:
- Created Blueprint path
- Variable, function, node, and connection counts
- Compilation status
- Any warnings from auto_layout or post-batch steps

## Handling Agent Results

If the agent's response includes a **Status** line:
- **completed** — present created artifacts to the user. Optionally verify key assets exist with a single search_assets call.
- **blocked** / **partial** — surface what was done, what remains, and what blocked it. The user may need to clean up partially created assets.

If the agent's response has no Status line (e.g., turn limit reached mid-response), treat as **partial** — summarize whatever the agent produced and warn that assets may be incomplete.
