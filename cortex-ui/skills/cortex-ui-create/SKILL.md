---
name: cortex-ui-create
description: Use when creating new widgets, screens, or UI components from a spec, mockup, or description
---

# UI Create

Creates UMG widget screens using the `create_widget_screen` composite tool via the UI Developer agent.

## Steps

### 1. Launch UI Developer Agent

Use the Task tool with `subagent_type: "cortex-ui:ui-developer"` to delegate UI creation.

Pass the full specification including:
- Screen type and name
- Complete widget hierarchy (panels, text blocks, buttons, images)
- Inline styling (text, fonts, colors, anchors, padding, brushes)
- Animations (fade in/out, transitions)

### 2. Agent Workflow (runs in background)

The UI Developer agent will:
1. Read `.cortex/domains/umg.md` for widget conventions and styling shorthand
2. Plan the widget hierarchy top-down
3. **Use `create_widget_screen` composite tool** — single call builds the entire screen
4. Review warnings from compilation
5. Report final result with widget tree and stats

**IMPORTANT:** The agent MUST use `create_widget_screen` for new screen creation. Individual tools (`add_widget`, `set_text`, `set_color`, `set_font`, `set_brush`, `set_padding`, `set_anchor`, `set_alignment`, `set_size`, `set_visibility`, `create_animation`) are PROHIBITED for new screen creation.

### 3. Review Agent Results

The agent returns:
- Created widget path
- Widget count, styling count, animation count
- Compilation status
- Any warnings from post-batch steps
