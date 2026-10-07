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

- `dump_tree(asset_path, include_transitions?, include_nodes?, inspect_instances?, inspect_section?, inspect_offset?, inspect_count?)`
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

## Stored Editor Inspection

Use the existing `dump_tree` routed command with `inspect_instances=True` to inspect stored editor definitions, instance values, parameters, and bindings. This is opt-in; omission defaults to `False` and retains the ordinary structural dump. Inspection is read-only: it does not compile, save, or edit the asset, and it does not report live execution state or runtime instance values.

Available stored fields depend on the engine version; stored execution-runtime data is not live runtime state. `definition_id_available=False` means `definition_id` is omitted on UE5.6; UE5.7+ can expose the native definition ID. For `execution_runtime_struct` and `execution_runtime_object`, `engine_member_available=False` with `available=False` identifies absent UE5.6 engine members, not fabricated empty values. With engine members present on UE5.7+, `engine_member_available=True` and `available` describes the actual stored slot. Preserve these availability distinctions; do not invent unavailable values or treat version-dependent absence as a failed read of an existing field.

For MCP, prefer section pages with `inspect_count=1`:

```python
statetree_cmd(command="dump_tree", params={
    "asset_path": "/Game/AI/StateTrees/ST_Guard",
    "inspect_instances": True,
    "inspect_section": "nodes",
    "inspect_offset": 0,
    "inspect_count": 1
})
```

| `inspect_section` | Stored entries |
|-------------------|----------------|
| `root` | One entry containing root metadata, root parameters and their identity, and subtree root identities |
| `states` | State metadata, parameters, and transitions across every non-null subtree; separately paged node bodies are omitted |
| `nodes` | Evaluators, global tasks, state tasks/single-task/enter conditions/considerations, and transition conditions, with owner identity |
| `bindings` | Stored property binding records |

Read every section and every page for a complete capture of the exposed reflected fields. Each native page reports `total`, `offset`, `returned_count`, `has_more`, and `entries`. Before advancing, require no transport `_truncated` marker and `len(entries) == returned_count`; only then advance by `returned_count` and trust `has_more`. The shared MCP formatter can shorten `entries` without reconciling these native top-level counts. If `_truncated` is present or the counts disagree, reduce `inspect_count` and recapture the same section/offset through MCP, down to count 1; do not advance past omitted entries or declare a complete capture. `inspect_offset` defaults to `0`, must be an integer in `0..2147483647`, and must not exceed the selected section's `total`; `inspect_count` defaults to `1` and must be an integer in `1..100`. An untruncated offset equal to `total` is a valid empty terminal page: `returned_count=0`, `has_more=False`, `entries=[]`.

Present values are strict: `inspect_instances` must be a JSON boolean; `inspect_section` must be exactly `root`, `states`, `nodes`, or `bindings`; offsets/counts must be finite integral JSON numbers, not strings, booleans, null, or fractional values. Malformed present fields and out-of-range offsets/counts return `INVALID_FIELD`, not default requests. A section requires `inspect_instances=True`; offset/count require both enabled inspection and a section. Omitting section and paging controls with inspection enabled requests the explicit native unpaged capture; it does not bypass MCP response limits.

Paging limits the number of entries serialized, not response bytes or characters. The existing shared MCP formatter has a **40,000-character** response limit; `inspect_count=1` is recommended, not a size guarantee. A single entry can exceed that limit, and a large unpaged capture can return `_error="RESPONSE_TOO_LARGE"` instead of inspection data. Use the existing section controls rather than the formatter's generic `limit` suggestion, which is not a `dump_tree` inspection parameter. If even a one-entry page is rejected, report that section/offset as blocked and the capture as incomplete; do not claim missing data is absent, invent values, or bypass MCP with direct TCP or Unreal Python. Native unpaged capability remains available, but arbitrary unpaged MCP payload sizes are not supported.

Preserve the `completeness` description and each field's `partial`/`issues` in findings. Unsupported values, depth-limited values, and identity-only references are not proof of absence. Ordinary UObject references and external linked assets expose identity only, not recursive object contents; the explicitly stored node instance-object and execution-runtime-object slots expose one level of reflected fields, whose own references remain identity-only. Inspection has a depth limit of 32, no native array-count truncation, and does not capture non-reflected engine caches. Engine availability markers distinguish unavailable members from present but empty slots; version-dependent absence alone is not a serialization failure. Even all pages cannot prove complete runtime state. This read capability does not add node, parameter, or binding authoring support.

Stored numeric inspection preserves actual uint32 fields exactly, including values above `INT32_MAX`. GUID consumers must preserve/recombine reflected 32-bit bit patterns: signed components, including negative values, are valid identity representations and must not be forced into unsigned display. Signed 64-bit integers within `-9007199254740991..9007199254740991` remain JSON numbers; values outside that safe-integer range are lossless decimal strings. Use reflected `cpp_type` to identify the original field type, and do not coerce those strings into lossy numbers. This representation applies to stored StateTree inspection, not runtime values or a changed shared Core serializer contract.

## State Selectors Across Subtrees

Prefer returned state GUIDs (`state_id`, `parent_state_id`, `source_state_id`, `target_state_id`, or `new_parent_state_id` as applicable) over human-readable paths. Ordinary dumps, reads, state mutations, and transition selectors address every non-null subtree in stored order, including later roots when the first root slot is null. Omitted root selectors retain the first valid root default. Duplicate paths across roots are ambiguous and must be resolved with a GUID, not guessed or treated as first-match. All-root lookup does not relax existing root deletion or reparenting restrictions.

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

- StateTree asset CRUD and opt-in stored editor instance/parameter/binding inspection
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
