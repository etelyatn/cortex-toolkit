---
name: cortex-ui-create
description: Use when creating new widgets, screens, or UI components from a spec, mockup, or description
---

# UI Create

Creates UMG widget hierarchies from specifications using the UI Developer agent.

## Steps

### 1. Launch UI Developer Agent

Use the Task tool with `subagent_type: "cortex-ui:ui-developer"` to delegate UI creation.

Pass the full specification including:
- Screen type (full screen menu, HUD overlay, dialog, popup)
- Widget hierarchy (panels, text blocks, buttons, images)
- Layout approach (anchored, box layouts, grids)
- Properties (text content, fonts, colors, anchors, padding)
- Interactions (button clicks, hover states)
- Animations (transitions, feedback)

Example prompts:
- "Create WBP_MainMenu with title, 3 buttons (Play, Settings, Quit), and background image"
- "Create a health bar HUD overlay with player name, HP bar, and portrait"
- "Create WBP_ConfirmDialog with message text, Cancel and Confirm buttons"
- "Build an inventory screen with grid layout, item slots, and detail panel"

### 2. Agent Workflow (runs in background)

The UI Developer agent will:
1. Read `.cortex/domains/umg.md` for project widget conventions and style guide
2. Identify base widget class or parent (e.g., `WBP_BaseScreen`)
3. Plan the widget hierarchy top-down
4. Create the Widget Blueprint (or verify it exists)
5. Build widget tree with proper nesting
6. Configure properties (anchors, alignment, padding, text, colors)
7. Add animations if specified
8. Compile and verify the widget

All MCP tool calls happen in the background — you won't see each individual call.

### 3. Review Agent Results

The agent returns:
- Created widget path
- Widget hierarchy tree
- Key properties set
- Animations added
- Compilation status

If the agent encounters issues (invalid widget class, layout conflicts), it will report them for you to address.

## Why Use the Agent?

- **Clean conversation** — no flood of MCP tool calls
- **Context-aware design** — agent follows project widget conventions and base classes
- **Hierarchy planning** — designs proper widget nesting automatically
- **Expandable details** — use Ctrl+O to see build steps if needed
