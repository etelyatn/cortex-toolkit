---
name: cortex-reparent
description: Use when reparenting Blueprints to a new parent class — changing inheritance hierarchy for one or multiple Blueprints
---

# Blueprint Reparent

Change the parent class of one or more Blueprints.

## Usage

`cortex-reparent BP_DecoCouch03 to BP_Seats_C` — Reparent one Blueprint
`cortex-reparent all children of BP_Seats to BP_Seats_C` — Reparent multiple

## Steps

### 1. Resolve Target Blueprints

If a **single Blueprint** is named:
- Search for the asset path using `search_assets` if only the short name is provided

If **"all children of X"** or **multiple Blueprints** are requested:
- Use `list_blueprints` filtered by path, or `search_assets` to find candidates
- For each candidate, call `get_blueprint_info` and check `parent_class`
- Filter to only those whose parent matches the old class

Present the list to the user for confirmation before proceeding.

### 2. Resolve New Parent

The new parent can be:
- A **Blueprint asset path** (e.g., `/Game/Blueprints/BP_Seats_C`)
- A **C++ class name** (e.g., `AMVSeat`, `AActor`)

Verify the new parent exists using `get_blueprint_info` (for BP) or `describe_class` (for C++).

### 3. Pre-Reparent: Capture SCS Component State

**CRITICAL**: Reparenting replaces the Blueprint's SCS (SimpleConstructionScript) component
templates with the new parent's SCS. This overwrites component defaults like meshes,
transforms, Enter/Exit locations, and other component properties.

For each Blueprint to reparent:

1. Call `get_blueprint_info` to check for custom variables, functions, and graph node counts
2. Find a **placed instance** of the Blueprint in the level
3. Capture ALL SCS component properties from the instance:
   - `StaticMesh.StaticMesh` (mesh asset)
   - `StaticMesh.RelativeLocation`
   - `StaticMesh.RelativeRotation`
   - `Enter.RelativeLocation`
   - `Enter.RelativeRotation`
   - `Exit.RelativeLocation`
   - `Exit.RelativeRotation`
   - Any other custom component properties

Store these values — they will be restored after reparent.

If the Blueprint has **custom variables or complex graph logic**, warn the user that
these may not be compatible with the new parent.

### 4. Execute Reparent

Call `reparent_blueprint` for each target:
```
reparent_blueprint(
    asset_path="/Game/.../BP_DecoCouch03",
    new_parent="/Game/.../BP_Seats_C"
)
```

If `reparent_blueprint` is not available, fall back to `cleanup_blueprint_migration`:
```
cleanup_blueprint_migration(
    asset_path="/Game/.../BP_DecoCouch03",
    new_parent_class="/Game/.../BP_Seats_C.BP_Seats_C_C"
)
```
Note: `cleanup_blueprint_migration` requires the **generated class path** (with `_C` suffix).

### 5. Post-Reparent: Restore SCS Component State

After reparent, the Blueprint and all placed instances have wrong component values
from the new parent's CDO. Restore in two layers:

**Layer 1 — BP defaults** (so new instances get correct values):
```python
blueprint_cmd(command="set_component_defaults", params={
    "asset_path": asset_path,
    "component_name": "CapturedOwnedMesh",
    "properties": {
        "StaticMesh": "/Game/Meshes/SM_Original.SM_Original",
        "RelativeLocation": {"X": 0, "Y": 0, "Z": 0},
        "RelativeRotation": {"Pitch": 0, "Yaw": 0, "Roll": 0},
        "bVisible": True
    },
    "compile": True,
    "save": False
})
```

Check `partial_failure` and `errors[]` after restoring component defaults. This command can only
restore owned SCS components on the reparented Blueprint; inherited/native parent components
cannot be restored through `set_component_defaults`.

**Layer 2 — Fix placed instances** (existing instances have baked overrides):
Use `level_compose` modify operations to restore ALL captured properties on EACH instance:
```python
level_compose(operations=[{
    "op": "modify",
    "actor": "InstanceLabel",
    "properties": {
        "StaticMesh.StaticMesh": "original/mesh/path",
        "StaticMesh.RelativeLocation": {"X": 0, "Y": 0, "Z": 0},
        "StaticMesh.RelativeRotation": {"Pitch": 0, "Yaw": 0, "Roll": 0},
        "Enter.RelativeLocation": {"X": 0, "Y": 105, "Z": -1.88},
        "Enter.RelativeRotation": {"Pitch": 0, "Yaw": 90, "Roll": 0},
        "Exit.RelativeLocation": {"X": 0, "Y": 55, "Z": 90},
        "Exit.RelativeRotation": {"Pitch": 0, "Yaw": 90, "Roll": 0}
    }
}])
```

### 6. Compile and Save

Compile and save each reparented Blueprint with the router command names:

```python
blueprint_cmd(command="compile", params={"asset_path": asset_path})
blueprint_cmd(command="save", params={"asset_path": asset_path})
```

### 7. Report Results

Present a summary table:

| Blueprint | Old Parent | New Parent | Instances Fixed | Status |
|-----------|-----------|------------|-----------------|--------|
| BP_DecoCouch05 | BP_Seats_C | BP_Seats_C_C | 2 | Reparented + Restored |

If any warnings (e.g., SCS root component conflict), list them and recommend
visual verification in the editor — especially Enter/Exit arrow directions.
