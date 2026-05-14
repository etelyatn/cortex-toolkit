# StateTree Patterns

Operational guidance for the UnrealCortex `CortexStateTree` domain.

## Tool Surface

Use `statetree_cmd(command="...", params={...})` for direct commands and `statetree_compose(...)` for multi-step create/update flows.

## Router Commands

Asset lifecycle:

- `list_assets(path_filter?, limit?)`
- `create_asset(asset_path, schema_class, root_name?, save?)`
- `duplicate_asset(asset_path, new_asset_path, save?)`
- `delete_asset(asset_path, dry_run?, force?, expected_fingerprint?)`

Inspection:

- `dump_tree(asset_path, include_transitions?, include_nodes?)`
- `get_state(asset_path, state_id? | state_path?)`
- `check_structure(asset_path)`

Validation and compile:

- `validate_asset(asset_path, save?, expected_fingerprint)`
- `compile(asset_path, save?, expected_fingerprint)`

State mutation:

- `add_state(asset_path, parent_state_id?, parent_state_path?, name, type?, tag?, enabled?, selection_behavior?, index?, compile?, save?, expected_fingerprint)`
- `remove_state(asset_path, state_id? | state_path?, remove_children?, compile?, save?, expected_fingerprint)`
- `rename_state(asset_path, state_id? | state_path?, name, compile?, save?, expected_fingerprint)`
- `move_state(asset_path, state_id? | state_path?, new_parent_state_id?, new_parent_state_path?, index?, compile?, save?, expected_fingerprint)`
- `set_state_properties(asset_path, state_id? | state_path?, properties, compile?, save?, expected_fingerprint)`

Transition mutation:

- `add_transition(asset_path, source_state_id? | source_state_path?, target_state_id? | target_state_path?, trigger?, event_tag?, priority?, compile?, save?, expected_fingerprint)`
- `remove_transition(asset_path, state_id? | state_path?, transition_id, compile?, save?, expected_fingerprint)`
- `set_transition_properties(asset_path, state_id? | state_path?, transition_id, properties, compile?, save?, expected_fingerprint)`

## Compose First

Use `statetree_compose` for new StateTrees or existing assets with multiple structure edits.

```python
statetree_compose(
    mode="create",
    asset_path="/Game/AI/StateTrees/ST_Guard",
    schema_class="/Script/GameplayStateTreeModule.StateTreeComponentSchema",
    root_name="Root",
    states=[
        {"name": "Patrol", "parent_state_path": "Root", "tag": "AI.State.Patrol"},
        {"name": "Chase", "parent_state_path": "Root", "tag": "AI.State.Chase"}
    ],
    transitions=[
        {
            "source_state_path": "Root/Patrol",
            "target_state_path": "Root/Chase",
            "trigger": "OnEvent",
            "event_tag": "AI.Event.SawTarget",
            "priority": "Normal"
        }
    ],
    validate=True,
    compile=True,
    save=True
)
```

For updates:

```python
statetree_compose(
    mode="update",
    asset_path="/Game/AI/StateTrees/ST_Guard",
    expected_fingerprint={"asset_path": "/Game/AI/StateTrees/ST_Guard", "hash": "CURRENT_HASH"},
    states=[
        {"name": "Search", "parent_state_path": "Root", "tag": "AI.State.Search"}
    ],
    transitions=[
        {
            "source_state_path": "Root/Chase",
            "target_state_path": "Root/Search",
            "trigger": "OnStateCompleted",
            "priority": "Normal"
        }
    ],
    validate=True,
    compile=True,
    save=True
)
```

## Fingerprints

Use the fingerprint returned by `dump_tree`, `check_structure`, `validate_asset`, `compile`, or any mutation. Pass it back as `expected_fingerprint` before every later mutation.

For runtime mutations, `expected_fingerprint` is required on `validate_asset`, `compile`, all state mutation commands, and all transition mutation commands. For `delete_asset`, it is required whenever `dry_run` is false.

If a fingerprint mismatch occurs, re-read with `dump_tree`, compare the changed structure, and retry only after reconciling the user-visible difference.

## Safe Review

Read-only review permits:

- `list_assets`
- `dump_tree`
- `get_state`
- `check_structure`
- `get_dependencies`
- `get_referencers`

Do not call `validate_asset` or `compile` during read-only review. Both can dirty assets.

## Current Boundary

Supported:

- StateTree asset CRUD
- State hierarchy and paths
- State tags and whitelisted state properties
- Simple transitions
- Gameplay Tag validation
- Structure validation and compile diagnostics

Not supported:

- Task, condition, evaluator, or global task authoring
- Parameter bag editing
- Property binding editing
- Arbitrary node instance property mutation
