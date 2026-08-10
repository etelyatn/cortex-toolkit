---
name: cortex-umg
description: Use when creating or reviewing UMG widgets, screens, or UI components
---

# UMG

Creates, modifies, and reviews UMG widget screens following the `resources/ui-development.md` guide.

## Mode Detection

| Request | Mode |
|---------|------|
| "Create a new screen", "Build WBP_X", "Add a dialog", spec or mockup provided | Create/Modify |
| "Review", "Audit", "Check", "Analyse", hierarchy/layout/naming questions | Review/Analyze |
| Ambiguous | Default to **Review** |

---

## Create / Modify Mode

### 1. Execute the Workflow

Read the `resources/ui-development.md` guide, then execute its workflow directly in this conversation.

Pass the full specification including:
- Screen type and name
- Complete widget hierarchy (panels, text blocks, buttons, images)
- Inline styling (text, fonts, colors, anchors, padding, brushes)
- Animations (fade in/out, transitions)

### 2. Workflow

Follow this workflow:
1. Read `.cortex/domains/umg.md` for widget conventions and styling shorthand
2. Plan the widget hierarchy top-down
3. **Use `widget_compose` composite tool** — single call builds the entire screen
4. Review warnings from compilation
5. Report final result with widget tree and stats

**IMPORTANT:**
- For NEW widget screens: MUST use `widget_compose`. Individual tools (`add_widget`, `set_text`, `set_color`, `set_font`, `set_brush`, `set_padding`, `set_anchor`, `set_alignment`, `set_size`, `set_visibility`, `create_animation`) are PROHIBITED.
- For EXISTING widgets with 2+ changes: MUST use `core_cmd(batch)` with `stop_on_error: true` and `$ref` wiring. Never make N sequential individual tool calls — use the batch pipeline (see `resources/batch-pipeline-guide.md`).
- Individual tools are only acceptable for a single isolated change on an existing widget.

### 3. Verify Results

The workflow produces:
- Created widget path
- Widget count, styling count, animation count
- Compilation status
- Any warnings from post-batch steps

---

## Review / Analyze Mode

### 1. Execute the Workflow

Read the `resources/ui-development.md` guide, then execute its workflow directly in this conversation.

Pass the review scope and focus:
- Specific widgets to review (if targeted)
- "Review all widgets in /Game/UI/" (if full project review)
- Specific concerns (naming, layout, anchors, animations, nesting)

Example prompts:
- "Review WBP_YourMainMenu for layout and naming issues"
- "Check all HUD widgets for proper anchor usage"
- "Review widget hierarchy depth in WBP_YourInventoryScreen"
- "Verify all UI screens follow project conventions"

### 2. Workflow

Follow this workflow:
1. Read `.cortex/domains/umg.md` for project widget conventions and screen inventory
2. Discover relevant Widget Blueprints
3. Inspect widget trees (hierarchy, nesting depth, panel usage)
4. Check properties (anchors, padding, fonts, visibility)
5. Verify naming conventions (descriptive names, no defaults)
6. Review animations (screen transitions, feedback)
7. Cross-reference against project style guide

### 3. Verify Results

Report findings grouped by widget and severity:
- **Errors:** Broken bindings, missing required widgets, invalid properties
- **Warnings:** Naming violations, deep nesting (>5 levels), missing anchors, inconsistent padding
- **Info:** Animation suggestions, layout optimizations, accessibility improvements

Each finding includes:
- Widget Blueprint path
- Widget element name
- Issue description
- Recommendation for fix
- Context from project conventions

---

## Handling Results

Report results to the user with a completion status:
- **completed** — present results to the user. For Create mode, optionally verify key assets exist with a single `search_assets` call.
- **blocked** / **partial** — surface what was done, what remains, and what blocked it. For Create mode, warn the user that assets may be incomplete.

If the work is interrupted mid-execution, treat it as **partial** — summarize what was produced and note the review or creation may be incomplete.
