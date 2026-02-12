# UMG Patterns

Layout patterns and widget hierarchy best practices for game UI.

## Common Screen Layouts

### Full Screen Menu (Main Menu, Settings)
```
Root: Overlay
├── BG: Image (anchor: full stretch)
├── Content: VerticalBox (anchor: center, alignment: center)
│   ├── Title: TextBlock
│   ├── Spacer
│   ├── ButtonList: VerticalBox
│   │   ├── BtnPlay: Button > TextBlock
│   │   ├── BtnSettings: Button > TextBlock
│   │   └── BtnQuit: Button > TextBlock
│   └── Footer: TextBlock (version info)
└── FadeOverlay: Image (for transitions)
```

### HUD
```
Root: CanvasPanel
├── TopLeft: VerticalBox (anchor: top-left)
│   ├── HealthBar: ProgressBar
│   └── ManaBar: ProgressBar
├── TopRight: HorizontalBox (anchor: top-right)
│   └── Minimap: Image
├── BottomCenter: HorizontalBox (anchor: bottom-center)
│   └── ActionBar: HorizontalBox
│       ├── Slot1-6: Button > Image
└── Center: Overlay (anchor: center)
    └── Crosshair: Image
```

### Dialog / Popup
```
Root: Overlay
├── DimBackground: Image (semi-transparent black)
└── DialogBox: VerticalBox (anchor: center, explicit size)
    ├── Header: HorizontalBox
    │   ├── Title: TextBlock
    │   └── BtnClose: Button > Image
    ├── Body: ScrollBox
    │   └── Content: TextBlock (or RichTextBlock)
    └── Actions: HorizontalBox
        ├── BtnCancel: Button > TextBlock
        └── BtnConfirm: Button > TextBlock
```

### Inventory Grid
```
Root: VerticalBox
├── Header: HorizontalBox
│   ├── Title: TextBlock
│   ├── Spacer
│   └── SortDropdown: ComboBox
├── Grid: ScrollBox
│   └── GridPanel: UniformGridPanel
│       └── Slots: WBP_InventorySlot (×N)
└── Footer: HorizontalBox
    └── SelectedItemInfo: TextBlock
```

## Widget Naming

| Type | Prefix | Example |
|------|--------|---------|
| TextBlock | `Txt` | `TxtPlayerName` |
| Button | `Btn` | `BtnStartGame` |
| Image | `Img` | `ImgAvatar` |
| ProgressBar | `PB` | `PBHealth` |
| ScrollBox | `Scroll` | `ScrollInventory` |
| Panel (any) | `Pnl` | `PnlHeader` |

## MCP Tool Workflows

### Build a Screen
```
add_widget (root panel) → add_widget (sections) → add_widget (content)
→ set_anchor (all) → set_padding (all) → set_text/color/font (content)
→ create_animation (transitions)
```

### Modify Existing Screen
```
get_tree → identify target widgets → set_property / add_widget / remove_widget
→ get_tree (verify)
```

### Duplicate and Customize
```
duplicate_widget → set_text / set_color (customize copy)
```
