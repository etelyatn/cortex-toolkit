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
