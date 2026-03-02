---
name: cortex-material-review
description: Use when reviewing material structure, parameter usage, graph complexity, instance hierarchies, or checking material best practices compliance
---

# Material Review

Reviews materials, instances, and parameter collections for structure, performance, and best practices using the Material Designer agent.

## Steps

### 1. Launch Material Designer Agent

<!-- Turn budget: REVIEW tier (max_turns=15) — read + analyze + report pattern -->
Use the Task tool with `subagent_type: "cortex-toolkit:material-developer"` and `max_turns: 15` to delegate material review.

Pass the review scope and focus:
- Specific materials to review (if targeted)
- "Review all materials in /Game/Materials/" (if full project review)
- Specific concerns (graph complexity, parameter usage, instance hierarchy, naming)

Example prompts:
- "Review M_Master_PBR for graph complexity and unused nodes"
- "Check all material instances for parameters that match parent defaults (redundant overrides)"
- "Review parameter collection usage across all materials"
- "Verify material naming conventions in /Game/Materials/"
- "Analyze instance hierarchy depth and parameter inheritance"

### 2. Agent Workflow (runs in background)

The Material Designer agent will:
1. Read `.cortex/domains/material.md` for project material conventions
2. Discover relevant material assets
3. Inspect expression graphs (node count, connection patterns, unused nodes)
4. Check parameter usage (exposed params, default values, override consistency)
5. Verify instance hierarchies (parent chains, redundant overrides)
6. Review parameter collections (unused parameters, naming)
7. Cross-reference against project material conventions

All MCP tool calls happen in the background — you won't see each individual call.

### 3. Review Agent Results

The agent returns findings grouped by material and severity:
- **Errors:** Missing parent materials, broken connections, invalid parameter types
- **Warnings:** Redundant instance overrides, unused expression nodes, deep instance chains, naming violations
- **Info:** Graph simplification suggestions, parameter organization improvements, collection consolidation opportunities

Each finding includes:
- Material asset path
- Issue description
- Recommendation for fix
- Context from project conventions

## Why Use the Agent?

- **Clean conversation** — no flood of MCP tool calls
- **Context-aware analysis** — agent applies project material conventions
- **Comprehensive checks** — systematic review of graphs, parameters, instances, collections
- **Expandable details** — use Ctrl+O to see inspection details if needed

## Handling Agent Results

If the agent's response includes a **Status** line:
- **completed** — present the findings to the user as-is.
- **blocked** / **partial** — surface what was done, what remains, and what blocked it. Let the user decide whether to re-invoke for the remaining scope.

If the agent's response has no Status line (e.g., turn limit reached mid-response), treat as **partial** — summarize whatever the agent produced and note that the review may be incomplete.
