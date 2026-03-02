---
name: cortex-bp-review
description: Use when reviewing Blueprint structure, complexity, naming conventions, or best practices compliance
---

# Blueprint Review

Reviews Blueprint assets for structure, naming, complexity, and UE best practices using the Blueprint Developer agent.

## Steps

### 1. Launch Blueprint Developer Agent

<!-- Turn budget: REVIEW tier (max_turns=15) — read + analyze + report pattern -->
Use the Task tool with `subagent_type: "cortex-toolkit:blueprint-developer"` and `max_turns: 15` to delegate Blueprint review.

Pass the review scope:
- Specific Blueprint paths to review (if targeted review)
- "Review all Blueprints in /Game/Blueprints/" (if full project review)
- Specific concerns to check (naming, complexity, compilation, variable organization)

Example prompts:
- "Review BP_PlayerCharacter for complexity and best practices"
- "Review all actor Blueprints in /Game/Characters/ for naming violations"
- "Check if BP_GameMode follows project conventions"

### 2. Agent Workflow (runs in background)

The Blueprint Developer agent will:
1. Read `.cortex/domains/blueprints.md` for project conventions
2. List and inspect relevant Blueprints
3. Check structure (naming, type appropriateness, parent class)
4. Analyze complexity (node counts per graph, variable counts)
5. Verify compilation status
6. Check variable organization (categories, exposure, naming)
7. Cross-reference against project conventions

All MCP tool calls happen in the background — you won't see each individual call.

### 3. Review Agent Results

The agent returns findings grouped by severity:
- **Errors:** Won't compile, broken references, critical issues
- **Warnings:** Naming violations, high complexity (>50 nodes/graph, >10 variables), missing categories
- **Info:** Optimization suggestions, C++ migration candidates

Each finding includes:
- Blueprint path
- Issue description
- Recommendation for fix
- Context from project conventions

## Why Use the Agent?

- **Clean conversation** — no flood of MCP tool calls
- **Context-aware analysis** — agent compares against project conventions
- **Comprehensive checks** — agent performs all standard review steps systematically
- **Expandable details** — use Ctrl+O to see inspection details if needed

## Handling Agent Results

If the agent's response includes a **Status** line:
- **completed** — present the findings to the user as-is.
- **blocked** / **partial** — surface what was done, what remains, and what blocked it. Let the user decide whether to re-invoke for the remaining scope.

If the agent's response has no Status line (e.g., turn limit reached mid-response), treat as **partial** — summarize whatever the agent produced and note that the review may be incomplete.
