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

### Control Slot Layout
```
get_schema (discover slot properties) → set_property with "slot." prefix
Example: set_property(property_path="slot.HorizontalAlignment", value="Center")
```

### Modify Existing Screen
```
get_tree → identify target widgets → set_property / add_widget / remove_widget
→ get_tree (verify)
```

### Inspect Widget Layout (get_widget)

`get_widget` returns full widget state. Key fields added in Group A:

```python
result = get_widget(asset_path="/Game/UI/WBP_HUD", widget_name="TxtScore")

# render_transform — always present
result["render_transform"]
# {
#   "translation": {"x": 0.0, "y": 0.0},
#   "scale":       {"x": 1.0, "y": 1.0},
#   "shear":       {"x": 0.0, "y": 0.0},
#   "angle":       0.0,
#   "pivot":       {"x": 0.5, "y": 0.5}
# }

# slot_type — always present, null for root widget
result["slot_type"]  # e.g. "CanvasPanelSlot", "HorizontalBoxSlot", null

# slot — layout details, depends on slot_type
result["slot"]
# CanvasPanelSlot example:
# {
#   "anchors":   {"min": {"x": 1.0, "y": 0.0}, "max": {"x": 1.0, "y": 0.0}},
#   "offsets":   {"left": -200.0, "top": 20.0, "right": 200.0, "bottom": 40.0},
#   "alignment": {"x": 1.0, "y": 0.0},
#   "z_order":   0,
#   "auto_size": false
# }
# HorizontalBoxSlot / VerticalBoxSlot / OverlaySlot example:
# {
#   "padding": {"left": 8.0, "top": 4.0, "right": 8.0, "bottom": 4.0}
# }
# null — root widget or unrecognized slot type
```

**Tip:** Check `slot_type` before reading `slot` to know which fields to expect.

### Duplicate and Customize
```
duplicate_widget → set_text / set_color (customize copy)
```

### Vertical Fill Child Pattern
```
Root: VerticalBox
├── Header: TextBlock (slot.Size.SizeRule = Auto)
└── Body: ScrollBox (slot.Size.SizeRule = Fill, slot.Size.Value = 1.0)
```

## Benchmark Tests

UMG domain workflows are validated by the benchmark testing framework in `Plugins/UnrealCortex/MCP/tests/`:

| Test File | Coverage |
|-----------|----------|
| `test_e2e.py` | Widget class listing, tree CRUD, property setters, schema queries |
| `test_umg_composites.py` | `create_widget_screen` composite end-to-end |
| `test_mcp_scenarios.py` | Widget Builder scenario (create + hierarchy + styling + verify) |

Run to validate after modifying UMG MCP tools or C++ command handlers.
