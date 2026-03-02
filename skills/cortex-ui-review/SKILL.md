---
name: cortex-ui-review
description: Use when reviewing widget hierarchy, layout patterns, UI structure, or checking UMG best practices compliance
---

# UI Review

Reviews UMG widget hierarchies for structure, layout patterns, and best practices using the UI Developer agent.

## Steps

### 1. Launch UI Developer Agent

<!-- Turn budget: REVIEW tier (max_turns=15) — read + analyze + report pattern -->
Use the Task tool with `subagent_type: "cortex-toolkit:ui-developer"` and `max_turns: 15` to delegate UI review.

Pass the review scope and focus:
- Specific widgets to review (if targeted)
- "Review all widgets in /Game/UI/" (if full project review)
- Specific concerns (naming, layout, anchors, animations, nesting)

Example prompts:
- "Review WBP_MainMenu for layout and naming issues"
- "Check all HUD widgets for proper anchor usage"
- "Review widget hierarchy depth in WBP_InventoryScreen"
- "Verify all UI screens follow project conventions"

### 2. Agent Workflow (runs in background)

The UI Developer agent will:
1. Read `.cortex/domains/umg.md` for project widget conventions and screen inventory
2. Discover relevant Widget Blueprints
3. Inspect widget trees (hierarchy, nesting depth, panel usage)
4. Check properties (anchors, padding, fonts, visibility)
5. Verify naming conventions (descriptive names, no defaults)
6. Review animations (screen transitions, feedback)
7. Cross-reference against project style guide

All MCP tool calls happen in the background — you won't see each individual call.

### 3. Review Agent Results

The agent returns findings grouped by widget and severity:
- **Errors:** Broken bindings, missing required widgets, invalid properties
- **Warnings:** Naming violations, deep nesting (>5 levels), missing anchors, inconsistent padding
- **Info:** Animation suggestions, layout optimizations, accessibility improvements

Each finding includes:
- Widget Blueprint path
- Widget element name
- Issue description
- Recommendation for fix
- Context from project conventions

## Why Use the Agent?

- **Clean conversation** — no flood of MCP tool calls
- **Context-aware analysis** — agent applies project widget conventions and style guide
- **Comprehensive checks** — systematic review of hierarchy, properties, naming, animations
- **Expandable details** — use Ctrl+O to see inspection details if needed

## Handling Agent Results

If the agent's response includes a **Status** line:
- **completed** — present the findings to the user as-is.
- **blocked** / **partial** — surface what was done, what remains, and what blocked it. Let the user decide whether to re-invoke for the remaining scope.

If the agent's response has no Status line (e.g., turn limit reached mid-response), treat as **partial** — summarize whatever the agent produced and note that the review may be incomplete.
