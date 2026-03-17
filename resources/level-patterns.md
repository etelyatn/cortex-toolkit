# Level Patterns

Common patterns and workflows for level design with UnrealCortex MCP tools.

## Actor Lifecycle Workflows

### Spawn and Configure (use level_compose)
```
level_compose(operations=[{"op": "spawn", ..., "folder": "...", "properties": {...}}])
```

### Spawn and Attach (use level_compose)
```
level_compose(operations=[
    {"op": "spawn", "id": "parent", ...},
    {"op": "spawn", "id": "child", ...},
    {"op": "attach", "actor": "$ops[child].name", "parent": "$ops[parent].name"}
])
```

### Single Actor Quick Edit (individual tools OK)
```
level_cmd("set_transform") → level_cmd("set_actor_property") → level_cmd("save_level")
```

### Duplicate and Offset
```
level_cmd("find_actors", params={"pattern": "Wall*"}) → level_compose (duplicate × N, with offset) → level_cmd("save_level")
```

### Delete with Safety Check
```
level_cmd("get_actor") → level_cmd("delete_actor", params={"actor": "...", "confirm_class": "StaticMeshActor"}) → level_cmd("save_level")
```

### Spawn into Sublevel
```
level_cmd("list_sublevels") → level_cmd("load_sublevel") (if needed) → level_cmd("spawn_actor", params={"class_name": "...", "level": "SublevelShortName"})
```

**Example: Spawn actor into a streaming sublevel**
```python
# Ensure sublevel is loaded
level_cmd(command="load_sublevel", params={"sublevel": "LVL_Cubic_Campus_BPs"})

# Spawn directly into the sublevel
level_cmd(command="spawn_actor", params={
    "class_name": "PointLight",
    "location": [100, 200, 300],
    "label": "CampusLight",
    "level": "LVL_Cubic_Campus_BPs"
})
```

**In level_compose:**
```python
level_compose(
    operations=[
        {"op": "spawn", "class": "PointLight", "label": "CampusLight",
         "location": [100, 200, 300], "level": "LVL_Cubic_Campus_BPs"}
    ],
    save=True
)
```

**Validation:** Sublevel must be loaded. Returns `InvalidValue` if sublevel not found or not loaded.

## Query Workflows

### Find Actors by Type
```
level_cmd("list_actors", params={"class_filter": "PointLight"}) → review results
```

### Spatial Query
```
level_cmd("list_actors", params={"region": {"type": "sphere", "center": [0,0,0], "radius": 1000}}) → review nearby actors
```

### Paginated Listing
```
level_cmd("list_actors", params={"limit": 50, "offset": 0}) → level_cmd("list_actors", params={"limit": 50, "offset": 50}) → ...
```

### Wildcard Search
```
level_cmd("find_actors", params={"pattern": "*Door*"}) → level_cmd("get_actor") → review details
```

### Bounding Box Analysis
```
level_cmd("get_bounds", params={"folder": "Geometry"}) → review spatial extent → plan new actor placement
```

## Organization Workflows

### Folder Organization
```
level_cmd("find_actors", params={"pattern": "Light*"}) → level_compose (modify × N, set folder "Lighting") → level_cmd("save_level")
```

### Actor Attachment
```
level_compose (spawn parent + spawn child + attach child to parent) → level_cmd("save_level")
```

### Grouping (Non-WP Levels Only)
```
level_cmd("list_actors", params={"tags": ["wall_section"]}) → level_cmd("group_actors") → level_cmd("save_level")
```

### Ungrouping
```
level_cmd("ungroup_actors", params={"group": "GroupActor_0"}) → level_cmd("save_level")
```

### Tagging
```
level_cmd("find_actors", params={"pattern": "*Destructible*"}) → level_compose (modify × N, set tags ["destructible", "physics"]) → level_cmd("save_level")
```

## Component Workflows

### Inspect Components
```
level_cmd("list_components", params={"actor": "..."}) → level_cmd("get_component_property", params={"actor": "...", "component": "...", "property_path": "..."})
```

### Add and Configure Component
```
level_cmd("add_component", params={"actor": "...", "class_name": "PointLightComponent"}) → level_cmd("set_component_property", params={"actor": "...", "component": "...", "property_path": "Intensity", "value": 5000}) → level_cmd("save_level")
```

### Remove Instance Component
```
level_cmd("list_components", params={"actor": "..."}) → level_cmd("remove_component", params={"actor": "...", "component": "..."}) → level_cmd("save_level")
```

**Note:** Only `Instance` creation method components can be removed. `Native` and `SimpleConstructionScript` components are permanent.

## Streaming Workflows

### Level Info and Sublevels
```
level_cmd("get_info") → level_cmd("list_sublevels") → review level structure
```

### Load/Unload Sublevel
```
level_cmd("list_sublevels") → level_cmd("load_sublevel", params={"sublevel": "SubLevel_Interior"}) → level_cmd("list_actors") (verify loaded)
```

### Toggle Sublevel Visibility
```
level_cmd("set_sublevel_visibility", params={"sublevel": "SubLevel_Lighting", "visible": false})
```

### Data Layer Assignment (World Partition)
```
level_cmd("list_data_layers") → level_cmd("set_data_layer", params={"actors": ["Actor1", "Actor2"], "data_layer": "Gameplay"}) → level_cmd("save_level")
```

## Scene Construction and Modification (level_compose)

### Multi-Actor Scene Creation

```python
level_compose(
    operations=[
        {
            "op": "spawn",
            "id": "sun",
            "class": "DirectionalLight",
            "rotation": [-45.0, 0.0, 0.0],
            "label": "Sun",
            "folder": "Lighting"
        },
        {
            "op": "spawn",
            "id": "sky",
            "class": "SkyLight",
            "location": [0.0, 0.0, 500.0],
            "label": "SkyLight",
            "folder": "Lighting"
        },
        {
            "op": "spawn",
            "id": "floor",
            "class": "StaticMeshActor",
            "location": [0.0, 0.0, 0.0],
            "scale": [10.0, 10.0, 1.0],
            "label": "Floor",
            "folder": "Geometry",
            "mesh": "/Engine/BasicShapes/Plane"
        }
    ],
    stop_on_error=True,
    save=True
)
```

### Scene with Attachments

```python
level_compose(
    operations=[
        {
            "op": "spawn",
            "id": "vehicle",
            "class": "StaticMeshActor",
            "location": [0.0, 0.0, 0.0],
            "label": "Vehicle_Body"
        },
        {
            "op": "spawn",
            "id": "turret",
            "class": "StaticMeshActor",
            "location": [0.0, 0.0, 100.0],
            "label": "Vehicle_Turret"
        },
        {
            "op": "attach",
            "actor": "$ops[turret].name",
            "parent": "$ops[vehicle].name"
        }
    ],
    stop_on_error=True,
    save=True
)
```

### Bulk Modification of Existing Actors

```python
level_compose(
    operations=[
        {"op": "modify", "actor": "Wall_North", "folder": "Geometry/Walls", "tags": ["wall"]},
        {"op": "modify", "actor": "Wall_South", "folder": "Geometry/Walls", "tags": ["wall"]},
        {"op": "modify", "actor": "Wall_East",  "folder": "Geometry/Walls", "tags": ["wall"]},
        {"op": "modify", "actor": "Wall_West",  "folder": "Geometry/Walls", "tags": ["wall"]}
    ],
    stop_on_error=False,
    save=True
)
```

### Mixed Create, Modify, Delete

```python
level_compose(
    operations=[
        {"op": "spawn", "id": "fill", "class": "PointLight",
         "label": "FillLight", "folder": "Lighting",
         "properties": {"PointLightComponent0.Intensity": 8000.0}},
        {"op": "modify", "actor": "KeyLight",
         "properties": {"PointLightComponent0.LightColor": {"R": 255, "G": 200, "B": 150, "A": 255}}},
        {"op": "delete", "actor": "OldRimLight"}
    ],
    stop_on_error=False,
    save=True
)
```

### Duplicate and Offset (Repeated Geometry)

```python
level_compose(
    operations=[
        {"op": "duplicate", "actor": "Wall_Section_A", "id": "wall_b", "offset": [200, 0, 0]},
        {"op": "duplicate", "actor": "Wall_Section_A", "id": "wall_c", "offset": [400, 0, 0]},
        {"op": "modify", "actor": "$ops[wall_b].name", "label": "Wall_Section_B"},
        {"op": "modify", "actor": "$ops[wall_c].name", "label": "Wall_Section_C"}
    ],
    stop_on_error=True,
    save=True
)
```

### Spawn with Component Properties

```python
level_compose(
    operations=[
        {
            "op": "spawn",
            "id": "light",
            "class": "PointLight",
            "location": [0.0, 0.0, 300.0],
            "label": "FillLight",
            "folder": "Lighting",
            "tags": ["indoor", "dynamic"],
            "properties": {
                "PointLightComponent0.Intensity": 8000.0,
                "PointLightComponent0.LightColor": {"R": 255, "G": 200, "B": 150, "A": 255}
            }
        }
    ]
)
```

**Property paths:** `"Component.Property"` -> `set_component_property`; `"Property"` -> `set_actor_property`.

## Response Format Reference

### Actor Summary (from list_actors, find_actors, select_actors, get_selection)
```json
{
  "name": "PointLight_0",
  "label": "PointLight_01",
  "class": "PointLight",
  "location": [100.0, 200.0, 300.0],
  "folder": "Lighting",
  "tags": ["dynamic"]
}
```

Key details:
- `class` is the **short name** (e.g., `"PointLight"`, not `"/Script/Engine.PointLight"`)
- `location` is an **[X, Y, Z] array** (not an object with x/y/z keys)

### Actor Details (from get_actor)
Includes all summary fields plus: `blueprint`, `rotation`, `scale`, `mobility`, `hidden`, `parent`, `components`, `component_count`.

### get_actor_property / set_actor_property
```json
{
  "actor": "PointLight_0",
  "property": "bHidden",
  "type": "bool",
  "value": false
}
```

Note: The response uses `actor` (not `name`) for the actor identifier field.

### list_components
```json
{
  "actor": "PointLight_0",
  "components": [...],
  "count": 3
}
```

Note: The count field is `count` (not `component_count`).

### list_sublevels
```json
{
  "sublevels": [
    {
      "name": "SubLevel_Interior",
      "path": "/Game/Maps/SubLevel_Interior",
      "is_loaded": true,
      "is_visible": true,
      "streaming_method": "LevelStreamingDynamic"
    }
  ],
  "count": 1
}
```

Note: Boolean fields are `is_loaded` and `is_visible` (with `is_` prefix).

### get_info
```json
{
  "level_name": "TestMap",
  "level_path": "/Game/Maps/TestMap",
  "world_type": "Editor",
  "actor_count": 42,
  "is_world_partition": false,
  "sublevels": 2,
  "world_settings": {
    "game_mode": "",
    "kill_z": -10000.0
  }
}
```

Note: Includes `sublevels` count and `world_settings` object with game mode and kill Z.

## Benchmark Tests

Level domain workflows are validated by the benchmark testing framework in `Plugins/UnrealCortex/MCP/tests/`:

| Test File | Coverage |
|-----------|----------|
| `test_level_e2e.py` | Actor lifecycle, transforms, components, queries (list, find, bounds, selection), streaming (sublevels, data layers) |
| `test_level_batch.py` | `level_compose` with spawn/modify/delete/duplicate/attach/detach, `$ops[]` refs, stop-on-error |
| `test_level_tools.py` | MCP tool wrappers for level operations |

Run to validate after modifying Level MCP tools or C++ command handlers.

## Common Pitfalls

- **Actor labels are not unique** -- if multiple actors share a label, use the full path from the `AmbiguousActor` error's `matches` array
- **Grouping fails in World Partition** -- check `get_info().is_world_partition` before calling `group_actors`
- **Cannot remove Native components** -- only Instance components (added at runtime or via Cortex) can be removed
- **Region filter format** -- sphere needs `center` + `radius`, box needs `center` + `extent` (half-size)
- **Sublevel parameter name** -- use `sublevel` (not `level`) for `load_sublevel`, `unload_sublevel`, `set_sublevel_visibility`
- **set_data_layer accepts actors array** -- pass `actors: ["Actor1", "Actor2"]` (list), not a single actor string
- **ungroup_actors accepts group name** -- pass `group: "GroupActor_0"` (string), not an actors list
- **Save after modifications** -- changes are in-memory until `save_level` or `save_all` is called
- **Location arrays** -- all vector fields (location, rotation, scale) use `[X, Y, Z]` array format, not objects
