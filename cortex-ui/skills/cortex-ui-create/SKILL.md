---
name: cortex-ui-create
description: Use when creating new widgets, screens, or UI components from a spec, mockup, or description
---

# UI Create

Creates UMG widget hierarchies from specifications.

## Before Starting

Read `.cortex/domains/umg.md` for project widget conventions, base classes, and style guide.

## Steps

### 1. Understand the Spec

Determine from the user's description:
- Screen type (full screen menu, HUD overlay, dialog, popup)
- Widget hierarchy (panels, text, buttons, images)
- Layout approach (anchored, boxed, grid)
- Interactions (button clicks, hover states)
- Animations (transitions, feedback)

### 2. Identify Base Widget

Check if the project has a base widget class (e.g., `WBP_BaseScreen`).
Use `list_widget_classes` to see available widget types.

### 3. Plan the Hierarchy

Design the widget tree top-down:
```
Root (CanvasPanel or Overlay)
├── Background (Image)
├── Content (VerticalBox or HorizontalBox)
│   ├── Header (TextBlock)
│   ├── Body (ScrollBox or panel)
│   └── Footer (HorizontalBox)
│       ├── BtnCancel (Button > TextBlock)
│       └── BtnConfirm (Button > TextBlock)
└── Overlay effects
```

### 4. Build the Widget

The Widget Blueprint must already exist (create in editor or via `create_blueprint` with UUserWidget parent).

Add widgets top-down:
```
add_widget(blueprint, parent_name, widget_class, widget_name)
```

Common widget classes: `CanvasPanel`, `VerticalBox`, `HorizontalBox`, `Overlay`, `TextBlock`, `Button`, `Image`, `Spacer`, `ScrollBox`

### 5. Set Properties

For each widget, configure:
- `set_anchor` — responsive positioning
- `set_alignment` — content alignment
- `set_padding` — spacing
- `set_size` — explicit sizing where needed
- `set_text` — text content
- `set_font` — typography
- `set_color` — colors
- `set_visibility` — initial visibility state

### 6. Add Animations

For screen transitions and feedback:
```
create_animation(blueprint, animation_name)
```

### 7. Verify

- `get_tree` — confirm hierarchy matches spec
- `get_widget` — spot-check key widget properties
- Compile the widget Blueprint
