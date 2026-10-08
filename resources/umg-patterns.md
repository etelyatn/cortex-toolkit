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

### Build a New Screen (widget_compose — mandatory for new Widget Blueprints)
```python
widget_compose(asset_path="/Game/UI/WBP_YourScreen", root_class="CanvasPanel", widgets=[...], animations=[...])
```
Creates the Widget Blueprint, adds the full hierarchy, applies styling, compiles, and saves — all in one atomic call.

### Build a Screen Incrementally (modifying existing widgets)
```python
umg_cmd(command="add_widget", params={"asset_path": "/Game/UI/WBP_Screen", "parent": "PnlContent", "class": "TextBlock", "name": "TxtTitle"})
umg_cmd(command="set_anchor", params={"asset_path": "/Game/UI/WBP_Screen", "widget_name": "TxtTitle", "anchor": "top_center"})
umg_cmd(command="set_text",   params={"asset_path": "/Game/UI/WBP_Screen", "widget_name": "TxtTitle", "text": "Hello"})
umg_cmd(command="create_animation", params={"asset_path": "/Game/UI/WBP_Screen", "animation_name": "FadeIn", "length": 0.3})
```

### Author Animation Content (guarded — opacity / color tracks)

`create_animation` creates only an **empty** named animation. Binding a Designer widget and
authoring its property tracks is a guarded `umg_cmd` sequence — never a hierarchy/style batch,
never a `widget_compose` animation entry, and never nested inside `core_cmd(batch)`. Each
authoring write (and each removal) consumes a full animation content-guard fingerprint
(signature **v2**) from `list_animation_bindings`; a stale or version-1 guard refuses without
mutation. `dry_run` defaults to **true**, so preview first and re-issue with `dry_run: false`.

```python
ASSET = "/Game/UI/WBP_Screen"

# 0. Create the empty animation (length in seconds). Existing animations: skip.
umg_cmd(command="create_animation", params={"asset_path": ASSET, "animation_name": "FadeIn", "length": 0.3})

# 1. Inspect: retain the animation content-guard fingerprint.
guard = umg_cmd(command="list_animation_bindings",
                params={"asset_path": ASSET, "animation_name": "FadeIn"})["fingerprint"]

# 2. Bind the ordinary Designer widget. "Decoration" is an Image here.
selector = umg_cmd(command="ensure_animation_binding",
                   params={"asset_path": ASSET, "animation_name": "FadeIn", "widget_name": "Decoration",
                           "expected_fingerprint": guard, "dry_run": False})["matched_selector"]
# selector = {binding_guid, widget_name, slot_widget_name: "", is_root_widget: false}

# 3. Author a float opacity track. Sections are half-open [start_seconds, end_seconds).
guard = umg_cmd(command="list_animation_bindings",
                params={"asset_path": ASSET, "animation_name": "FadeIn"})["fingerprint"]
umg_cmd(command="set_animation_property_track",
        params={"asset_path": ASSET, "animation_name": "FadeIn", "selector": selector,
                "property_path": "RenderOpacity",
                "track": {"type": "float", "sections": [{
                    "start_seconds": 0.0, "end_seconds": 0.3, "keys": [
                        {"time_seconds": 0.0, "value": 0.0, "interpolation": "linear"},
                        {"time_seconds": 0.3, "value": 1.0, "interpolation": "linear"}]}]},
                "expected_fingerprint": guard, "dry_run": False})

# 4. Author a linear-color track (four independent RGBA channels) on the same Image.
guard = umg_cmd(command="list_animation_bindings",
                params={"asset_path": ASSET, "animation_name": "FadeIn"})["fingerprint"]
umg_cmd(command="set_animation_property_track",
        params={"asset_path": ASSET, "animation_name": "FadeIn", "selector": selector,
                "property_path": "ColorAndOpacity",
                "track": {"type": "color", "sections": [{
                    "start_seconds": 0.0, "end_seconds": 0.3, "keys": [
                        {"time_seconds": 0.0, "value": {"r": 0.0, "g": 0.0, "b": 0.0, "a": 1.0}, "interpolation": "linear"},
                        {"time_seconds": 0.3, "value": {"r": 1.0, "g": 0.5, "b": 0.25, "a": 1.0}, "interpolation": "linear"}]}]},
                "expected_fingerprint": guard, "dry_run": False})

# 5. Persist explicitly — authoring never compiles or saves implicitly.
blueprint_cmd(command="compile", params={"asset_path": ASSET})
blueprint_cmd(command="save", params={"asset_path": ASSET})
```

Authoring contract limits:

- **Ordinary named Designer widgets only** — `is_root_widget` must be `false` and
  `slot_widget_name` empty. `is_root_widget=true` user-widget bindings, slot bindings and
  dynamic bindings are out of scope.
- **`float` and linear-color (`FLinearColor`) tracks only**; `linear` or `constant` interpolation,
  no cubic. Color keys use linear RGBA objects with exactly `r`/`g`/`b`/`a`.
- **At most 8 sections and 64 logical keys per track**; a color track expands to four channels.
  Times are quantized to the MovieScene tick resolution; sections are half-open `[start, end)`
  with `start < end`.
- **`track: null` clears exactly one property track** and keeps the binding. Removing the whole
  binding record (and its possessable/tracks) is `remove_animation_binding`.
- Inspect the authored result with
  `umg_cmd(command="list_animation_bindings", params={"asset_path": ASSET, "animation_name": "FadeIn", "include_track_content": True})`.
  A detailed read that exceeds the response ceiling returns `_error: "RESPONSE_TOO_LARGE"` with
  `reader_complete: false` and summary counts — not a silently truncated page.
- After any hierarchy/style batch or `widget_compose`, take a **fresh** fingerprint before the
  first guarded animation write.

### Control Slot Layout
```python
# Discover slot properties first
umg_cmd(command="get_schema", params={"asset_path": "/Game/UI/WBP_Screen", "widget_name": "TxtTitle"})

# Read a slot property
umg_cmd(command="get_property", params={"asset_path": "/Game/UI/WBP_Screen", "widget_name": "TxtTitle", "property_path": "slot.Padding.Left"})

# Write a slot property
umg_cmd(command="set_property", params={"asset_path": "/Game/UI/WBP_Screen", "widget_name": "TxtTitle", "property_path": "slot.HorizontalAlignment", "value": "Center"})
```

### Modify Existing Screen
```python
umg_cmd(command="get_tree",       params={"asset_path": "/Game/UI/WBP_Screen"})
# identify target widgets, then:
umg_cmd(command="set_property",   params={"asset_path": "/Game/UI/WBP_Screen", "widget_name": "TxtTitle", "property_path": "ColorAndOpacity.R", "value": 1.0})
umg_cmd(command="add_widget",     params={"asset_path": "/Game/UI/WBP_Screen", "parent": "PnlRoot", "class": "Button", "name": "BtnConfirm"})
umg_cmd(command="remove_widget",  params={"asset_path": "/Game/UI/WBP_Screen", "widget_name": "BtnOld"})
umg_cmd(command="get_tree",       params={"asset_path": "/Game/UI/WBP_Screen"})  # verify
```

### Inspect Widget Layout (get_widget)

`get_widget` returns full widget state including render transform and slot details:

```python
umg_cmd(command="get_widget", params={"asset_path": "/Game/UI/WBP_HUD", "widget_name": "TxtScore"})
# Response includes:
# render_transform — always present
# {
#   "translation": {"x": 0.0, "y": 0.0},
#   "scale":       {"x": 1.0, "y": 1.0},
#   "shear":       {"x": 0.0, "y": 0.0},
#   "angle":       0.0,
#   "pivot":       {"x": 0.5, "y": 0.5}
# }
#
# slot_type — always present, null for root widget
# e.g. "CanvasPanelSlot", "HorizontalBoxSlot", null
#
# slot — layout details, depends on slot_type
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

### Inspect and Set Designer Property Bindings

Reuse `umg_cmd`; property bindings are distinct from animation bindings and literal property values.

```python
state = umg_cmd(command="get_widget", params={
    "asset_path": "/Game/UI/WBP_HUD", "widget_name": "ProgressDisplay",
    "include_property_bindings": True,
})
# Require property_binding_state.reader_complete=true; retain its fingerprint.
umg_cmd(command="set_property_binding", params={
    "asset_path": "/Game/UI/WBP_HUD", "widget_name": "ProgressDisplay",
    "property_name": "Percent", "binding": None,
    "expected_fingerprint": state["property_binding_state"]["fingerprint"],
})
```

Explicit `binding=None` clears; `{}` or omitted `binding` refuses. An object authors a
binding: `{"kind":"property","source_path":["ElapsedValue"]}` or
`{"kind":"function","function_name":"GetElapsedPercent"}`. Sources must exist and be
compatible; property-bound functions must be pure/const. Compile source declarations
explicitly first when necessary. Re-inspect before each write; duplicates and stale
fingerprints refuse without mutation.

Use `get_tree(include_property_bindings=True)` for asset-wide inspection, including
records targeting deleted widgets. Unresolved source identities remain visible.
Oversized inspection returns `RESPONSE_TOO_LARGE` with false reader completeness, not
an empty list; orphan records cannot be recovered through missing-widget reads.
Pagination fields are unsupported. No implicit compile/save/reload: compile and save
explicitly through existing Blueprint/Core commands. Literal `set_property` does not
clear a binding.

### Duplicate and Customize
```python
umg_cmd(command="duplicate_widget", params={"asset_path": "/Game/UI/WBP_Screen", "widget_name": "BtnTemplate", "new_name": "BtnVariant"})
umg_cmd(command="set_text",  params={"asset_path": "/Game/UI/WBP_Screen", "widget_name": "BtnVariant", "text": "Variant"})
umg_cmd(command="set_color", params={"asset_path": "/Game/UI/WBP_Screen", "widget_name": "BtnVariant", "r": 0.2, "g": 0.8, "b": 0.2})
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
| `test_umg_composites.py` | `widget_compose` composite end-to-end |
| `test_mcp_scenarios.py` | Widget Builder scenario (create + hierarchy + styling + verify) |

Run to validate after modifying UMG MCP tools or C++ command handlers.
