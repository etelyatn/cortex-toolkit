---
name: cortex-ui-review
description: Use when reviewing widget hierarchy, layout patterns, UI structure, or checking UMG best practices compliance
---

# UI Review

Reviews UMG widget hierarchies for structure, layout patterns, and best practices.

## Before Starting

Read `.cortex/domains/umg.md` for project-specific widget conventions and screen inventory.

## Steps

### 1. Discover Widgets

Use `search_assets` with class filter for Widget Blueprints, or `list_blueprints` filtered to UI path.

### 2. Inspect Widget Tree

For each widget under review:
- `get_tree` — examine the full widget hierarchy
- Check nesting depth (>5 levels may indicate over-nesting)
- Verify layout panels are used correctly (Canvas, Vertical/Horizontal Box, Overlay)

### 3. Check Properties

For key widgets:
- `get_widget` — inspect properties of specific widgets
- Verify anchors are set correctly (responsive layouts)
- Check padding consistency
- Verify text widgets have proper font settings

### 4. Check Naming

- Widget names should describe their purpose: `TxtPlayerName`, `BtnStartGame`
- Avoid default names: `TextBlock_0`, `Button_1`
- Follow project conventions from `.cortex/domains/umg.md`

### 5. Review Animations

- `list_animations` — check for animation assets
- Verify animations cover key UX moments (screen enter/exit, feedback)

### 6. Report

Group findings by widget:
- **Errors:** Broken bindings, missing required widgets
- **Warnings:** Naming violations, deep nesting, missing anchors
- **Info:** Animation suggestions, layout optimizations
