---
name: cortex-data-review
description: Use when reviewing DataTables or DataAssets for balance issues, naming convention violations, structural problems, or data integrity checks
---

# Data Review

Reviews DataTables, DataAssets, and related data for quality and balance issues using the Data Balancer agent.

## Steps

### 1. Launch Data Balancer Agent

<!-- Turn budget: REVIEW tier (max_turns=15) — read + analyze + report pattern -->
Use the Task tool with `subagent_type: "cortex-toolkit:data-balancer"` and `max_turns: 15` to delegate data review.

Pass the review scope and focus:
- Specific assets to review (if targeted)
- "Review all DataTables for balance issues" (if full project review)
- Specific concerns (naming, balance, structure, data integrity)

Example prompts:
- "Review DT_WeaponStats for balance issues across all levels"
- "Check all quest DataTables for reward scaling problems"
- "Review data assets for naming violations and broken references"
- "Analyze XP progression curve in CT_LevelCurve"

### 2. Agent Workflow (runs in background)

The Data Balancer agent will:
1. Read `.cortex/domains/data.md` for project schemas, balance rules, naming conventions
2. Discover relevant data assets (DataTables, DataAssets, CurveTables, StringTables)
3. Check naming conventions against project patterns
4. Review structure (schemas, row counts, field population)
5. Perform balance analysis against defined rules
6. Cross-reference related tables for consistency
7. Validate GameplayTags used in data
8. Flag outliers, missing data, broken references

All MCP tool calls happen in the background — you won't see each individual call.

### 3. Review Agent Results

The agent returns findings grouped by severity:
- **Errors:** Missing data, broken references, invalid GameplayTags, critical issues
- **Warnings:** Naming violations, potential balance issues, outlier values
- **Info:** Suggestions for improvement, optimization opportunities

Each finding includes:
- Asset path and row name
- Field values and issue description
- Recommendation for fix
- Context from balance rules

## Why Use the Agent?

- **Clean conversation** — no flood of MCP tool calls
- **Context-aware analysis** — agent applies project balance rules and naming conventions
- **Cross-table validation** — checks consistency across related tables
- **Expandable details** — use Ctrl+O to see inspection details if needed

## Handling Agent Results

If the agent's response includes a **Status** line:
- **completed** — present the findings to the user as-is.
- **blocked** / **partial** — surface what was done, what remains, and what blocked it. Let the user decide whether to re-invoke for the remaining scope.

If the agent's response has no Status line (e.g., turn limit reached mid-response), treat as **partial** — summarize whatever the agent produced and note that the review may be incomplete.
