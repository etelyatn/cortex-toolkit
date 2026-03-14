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
set_transform -> set_actor_property -> save_level
```

### Duplicate and Offset
```
find_actors("Wall*") → duplicate_actor (x N, with offset) → save_level
```

### Delete with Safety Check
```
get_actor → delete_actor(actor, confirm_class="StaticMeshActor") → save_level
```

## Query Workflows

### Find Actors by Type
```
list_actors(class_filter="PointLight") → review results
```

### Spatial Query
```
list_actors(region={"type": "sphere", "center": [0,0,0], "radius": 1000}) → review nearby actors
```

### Paginated Listing
```
list_actors(limit=50, offset=0) → list_actors(limit=50, offset=50) → ...
```

### Wildcard Search
```
find_actors("*Door*") → get_actor(match) → review details
```

### Bounding Box Analysis
```
get_bounds(folder="Geometry") → review spatial extent → plan new actor placement
```

## Organization Workflows

### Folder Organization
```
find_actors("Light*") → set_folder(actor, "Lighting") (x N) → save_level
```

### Actor Attachment
```
spawn_actor (parent) → spawn_actor (child) → attach_actor(child, parent) → save_level
```

### Grouping (Non-WP Levels Only)
```
list_actors(tags=["wall_section"]) → group_actors(actors) → save_level
```

### Ungrouping
```
ungroup_actors(group="GroupActor_0") → save_level
```

### Tagging
```
find_actors("*Destructible*") → set_tags(actor, ["destructible", "physics"]) (x N) → save_level
```

## Component Workflows

### Inspect Components
```
list_components(actor) → get_component_property(actor, component, property)
```

### Add and Configure Component
```
add_component(actor, "PointLightComponent") → set_component_property(actor, component, "Intensity", 5000) → save_level
```

### Remove Instance Component
```
list_components(actor) → remove_component(actor, component) → save_level
```

**Note:** Only `Instance` creation method components can be removed. `Native` and `SimpleConstructionScript` components are permanent.

## Streaming Workflows

### Level Info and Sublevels
```
get_info → list_sublevels → review level structure
```

### Load/Unload Sublevel
```
list_sublevels → load_sublevel(sublevel="SubLevel_Interior") → list_actors (verify loaded)
```

### Toggle Sublevel Visibility
```
set_sublevel_visibility(sublevel="SubLevel_Lighting", visible=false)
```

### Data Layer Assignment (World Partition)
```
list_data_layers → set_data_layer(actors=["Actor1", "Actor2"], data_layer="Gameplay") → save_level
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
