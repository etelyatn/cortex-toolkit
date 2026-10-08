# UMG Domain Context
> Fill in the sections below. Delete the HTML comment examples as you go.
> Agents read this file before every task.

<!-- UI-specific knowledge for UI agents. -->

## Screen Inventory

<!-- WHY: Agents need to know what screens already exist before creating or modifying UI.
     List every Widget Blueprint with a one-line purpose. Without this list, agents
     may create duplicate screens or build from scratch when they should extend an existing one. -->
<!-- Example:
- WBP_YourMainMenu — main menu with Play, Settings, Quit
- WBP_YourHUD — in-game HUD with health, mana, minimap
- WBP_YourInventoryScreen — grid-based inventory
- WBP_YourDialogBox — reusable dialog popup
-->

## Style Guide

<!-- WHY: Consistent fonts, colors, and spacing make the UI feel cohesive.
     Agents apply these values when creating or styling widgets — without a
     style guide they will guess, producing inconsistent results.
     Include font families and sizes, primary/accent colors (hex or 0–1 float),
     button padding, corner radii, and any transition durations. -->
<!-- Example:
- Primary font: Roboto, 24pt for headers, 16pt for body
- Primary color: #2196F3 (blue), accent: #FF9800 (orange)
- Button padding: 16px horizontal, 8px vertical
- All screens fade in/out over 0.3s using a FadeIn/FadeOut animation
-->

## Base Classes

<!-- WHY: Agents need to know which base Widget Blueprints to extend rather than
     building from raw UserWidget. Extending a base class ensures inherited
     functionality (common events, shared styling) is not accidentally bypassed.
     List each base class with its purpose and what screens use it. -->
<!-- Example:
- WBP_YourBaseScreen: all full-screen widgets inherit from this (handles input focus, fade animations)
- WBP_YourBasePopup: all popups inherit from this (dim background, close button logic)
-->

## Animation Conventions

<!-- WHY: Animations bind to specific widgets or slot properties. When refactoring
     or deleting widgets, animation bindings must be cleanly updated to avoid orphaned
     tracks or missing target warnings.
     Use umg.list_animation_bindings to inspect bindings and umg.remove_animation_binding
     to safely prune bindings before deleting or renaming widgets. -->
<!-- Example:
- Intro / Outro: standard 0.3s FadeIn and FadeOut animations bound to RenderOpacity
- Hover feedback: button hover animations bound to Scale or ColorAndOpacity
- Binding removal vs track deletion: `remove_animation_binding` removes an entire target-binding record, not an individual property track.
  - Unshared binding: if a widget target has multiple property tracks (e.g., RenderOpacity and Scale) under a single binding record, removing that binding removes the possessable and all associated tracks.
  - Shared possessable: a possessable and its tracks are retained only while another UMG binding record still references its GUID. When multiple UMG binding records share the same GUID, removing one binding record preserves the shared MovieScene possessable and tracks for the remaining records.
  - Renaming a Designer widget (`umg.rename_widget`) propagates the binding record's WidgetName and its possessable; prefer it over delete/recreate. A stale animation content-guard fingerprint refuses without mutation.
  - Author new binding/track content through the guarded `umg.ensure_animation_binding` and
    `umg.set_animation_property_track` sequence: inspect with `umg.list_animation_bindings` to get the
    version-2 content-guard fingerprint, preview with `dry_run` (default true), apply, then compile
    and save explicitly. Ordinary named Designer widgets only (`float` / `FLinearColor` tracks,
    linear/constant keys, at most 8 sections and 64 logical keys per track); `track: null` clears one
    property track and keeps the binding. Authoring is a guarded transaction performed after any
    hierarchy/style batch or `widget_compose`, never inside one.
-->

## Designer Property Binding Conventions

<!-- WHY: A literal property write does not retire a serialized Designer binding.
     Inspect through umg.get_widget or umg.get_tree with include_property_bindings=true.
     get_tree includes orphan targets and unresolved sources. Require reader_complete=true
     and pass the returned asset-level fingerprint to umg.set_property_binding.
     Explicit binding=null clears; a validated object creates/replaces. Empty/omitted
     binding is not clear. Missing widgets, ambiguous targets and stale guards refuse.
     Clear before retiring source members, then compile/save explicitly and inspect a
     freshly loaded asset. Do not change literal defaults, hierarchy, styles or animations
     as a binding-removal workaround. See resources/umg-patterns.md for payloads. -->
