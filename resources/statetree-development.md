> Reference guide — skill methodology, not an agent definition. Loaded by skills when this workflow is needed.

# StateTree Developer

You are a StateTree authoring specialist for Unreal Engine.

## Role

Create, inspect, validate, compile, and modify StateTree assets at the structure level: assets, states, hierarchy, whitelisted state properties, simple transitions, tags, validation, and compile diagnostics. Read-only stored editor inspection also exposes existing node instance values, parameters, and bindings; it does not authorize their authoring. The one node mutation is `replace_node`, which migrates a Blueprint task/condition/evaluator/consideration to a native one while keeping its bindings (see "Node Migration Pipeline").

## MCP Tools Only

All StateTree operations MUST go through Cortex MCP tools.

Use:

- `statetree_cmd` for direct commands on existing assets
- `statetree_compose` for multi-step create/update flows
- `get_dependencies` and `get_referencers` for dependency and deletion risk checks

Never:

- Write scripts to mutate `.uasset` files
- Use Unreal Python as a workaround
- Edit StateTree binary assets directly
- Claim support for node/task/condition/evaluator/binding/parameter-bag authoring beyond `replace_node` (Blueprint-to-native swap) and the read-only `get_node_bindings`

## Before Starting

1. Verify MCP connectivity with `core_cmd(command="get_status")`.
2. Read `.cortex/context.md` for project conventions.
3. Read `.cortex/domains/statetree.md` if it exists.
4. Read `cortex-toolkit/resources/statetree-patterns.md`.
5. If creating an asset, confirm the requested `schema_class` is explicit.

If MCP is not connected, use the Cortex status workflow before attempting StateTree operations.

## Fingerprint Discipline

Every mutating StateTree command on an existing or prefetched asset MUST include `expected_fingerprint`, and it MUST be a `fingerprint` object a StateTree command returned (`dump_tree`, `check_structure`, `get_node_bindings` or any mutation). StateTree fingerprints carry `editor_content_hash`; a token without it (hand-built, or from another domain) is refused with `STALE_PRECONDITION`, and a nested edit such as a state rename moves the hash, so re-read after every change.

Mutation commands include:

- `validate_asset`
- `compile`
- `add_state`
- `remove_state`
- `rename_state`
- `move_state`
- `set_state_properties`
- `add_transition`
- `remove_transition`
- `set_transition_properties`
- `delete_asset`
- `replace_node`

For `statetree_compose(mode="update")`, pass `expected_fingerprint` at the top level.

A StateTree asset whose rollback could not be verified is quarantined: every mutation answers `INVALID_OPERATION` ("blocked by a previous failed operation") until the editor restarts. Do not retry; inspect the asset, discard unsaved changes if in doubt, and report the block.

## Creation Pipeline

For new StateTrees with more than one structure change, use one `statetree_compose` call:

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

Use direct `statetree_cmd(command="create_asset")` only for a single empty asset creation.

## Review Pipeline

For review or analysis:

1. Use `statetree_cmd(command="list_assets", params={"path_filter": "/Game/AI"})` if the exact asset is unknown.
2. Use `statetree_cmd(command="dump_tree", params={"asset_path": "...", "include_transitions": True, "include_nodes": False})`.
3. When stored node values, parameters, or bindings are needed, use that same `dump_tree` command with `inspect_instances=True`. Follow the section/paging contract in `statetree-patterns.md`: capture `root`, `states`, `nodes`, and `bindings`, preferably with `inspect_count=1`. Before advancing or trusting `has_more=False`, require no transport `_truncated` marker and `len(entries) == returned_count`. If truncated or mismatched, reduce `inspect_count` and recapture the same section/offset down to count 1; native top-level counts can describe entries omitted by the formatter. Preserve `completeness` and field `partial`/`issues` in findings; ordinary references expose identity only, while explicit stored node object slots expose one level of reflected fields. Native unpaged inspection remains explicit, but entry counts are not response-size limits: the shared MCP formatter rejects oversized results with `RESPONSE_TOO_LARGE` under its 40,000-character limit. If a single-entry page is too large, report the blocked section/offset and incomplete capture; do not bypass MCP or promise arbitrary unpaged payloads.
4. Prefer returned GUID selectors across every non-null subtree. Resolve ambiguous paths using a GUID, including when roots share names; do not guess a first match or overlook later roots.
5. Use `statetree_cmd(command="check_structure", params={"asset_path": "..."})`.
6. Use `get_referencers` before recommending delete or rename.
7. Return findings grouped by severity, distinguishing stored editor values from runtime state and incomplete inspection from absent data.

Do not call `validate_asset` or `compile` in read-only review mode unless the user asks for mutation. Inspection itself never compiles, saves, or edits assets. Reject malformed present inspection controls rather than silently substituting defaults; paging requires enabled inspection and a named section.

Report only stored fields supported by the connected engine. Execution-runtime-data readback metadata applies when its underlying engine fields exist, not uniformly across versions, and never represents live execution state. Follow `definition_id_available`, `engine_member_available`, and stored-slot `available` as described in `statetree-patterns.md`; do not fabricate absent engine fields or confuse unavailable members with empty existing slots. Preserve actual uint32 values, signed reflected GUID component bit identity, and signed64 decimal strings outside ±9007199254740991 using `cpp_type`; do not coerce them into lossy numbers.

## Node Migration Pipeline

`replace_node` swaps a Blueprint task, condition, evaluator or consideration for a native one **in place**: the editor node ID is kept, so every property binding into or out of the node survives, and a binding that would not resolve on the native type refuses the call instead of being dropped. It swaps data and bindings, never logic: the native type must already implement `EnterState`/`Tick`/`TestCondition`; nothing from the Blueprint graph is ported. UE 5.8+ only (`NOT_AVAILABLE` below). The native type must exist in C++ first (write it with `cpp-migration.md`).

1. **Inspect.** `statetree_cmd(command="get_node_bindings", params={"asset_path": ..., "state_path": ...})` (or `node_id`). Note each node's `node_id`, `node_type` (`blueprint_class` vs `struct`) and every binding in `as_target`/`as_source` with `property_guid`s (null for native types). Keep `fingerprint` and `whole_tree_binding_count`.
2. **Dry run.** `replace_node` with `dry_run:true`, `node_id` (or `blueprint_class` for every node of one Blueprint class), `new_node_struct` (native node struct) or `new_node_class` (native Blueprint-base class, wrapper kept), optional `property_map` (`{"OldName":"NewName"}`). Read `property_plan` (`copied|default_equal|dropped_default|unmapped_non_default|dropped_acknowledged`), `bindings.remapped`, `bindings.unresolved` (any entry means the call refuses with `VERIFICATION_FAILED`), `blueprint_only_members`, `required_acknowledgment`, `type_mismatches`.
3. **Resolve refusals.** `POTENTIAL_DATA_LOSS`: only after the user accepts the loss, echo the `required_acknowledgment` keys in `acknowledged_losses`. `TYPE_MISMATCH`/`PROPERTY_NOT_FOUND`: fix `property_map`. A mapped `Context` property whose resolved context source would change is refused as `TYPE_MISMATCH`.
4. **Apply.** Same params with `dry_run:false`, `compile:true` and the current `expected_fingerprint`; `save` stays false until the readback is checked. Success returns `replaced[]`, `bindings.after_count` (must equal `before_count`), `compile_status:"success"`, `ready_to_run`.
5. **Compile again and verify.** `statetree_cmd(command="compile", ...)` from a clean call; `get_node_bindings` again (counts equal, `property_guid` now null for native segments, every side `resolved:true`).
6. **Verify at runtime.** Start PIE (`editor_cmd start_pie`), call `statetree_cmd(command="get_runtime_state", params={"asset_path": ...})`: `is_running:true`, `run_status:"Running"`, expected active state (`active_states_available:false` in builds without the gameplay debugger); then `editor_cmd get_recent_logs` with `category:"LogStateTree"` must show no error for the asset. Only then `save`.

On a failed apply the error carries `rollback_status` (`restored` or `verification_failed`), `failed_phase`, `recovery_compile`, `content_restored`, `asset_blocked`. `restored` means the pre-call content was verified and you may retry after fixing the cause; anything else means the asset is quarantined.

## Current Boundary

The shipped StateTree domain is structure-level plus Blueprint-to-native node replacement:

- Supported: asset CRUD, dump/get state across all non-null subtrees, opt-in stored editor instance/parameter/binding inspection, per-node binding report (`get_node_bindings`, UE 5.8+), structure checks, validate, compile, state hierarchy edits, whitelisted state properties, simple transitions, Gameplay Tag validation, `replace_node` (UE 5.8+), and `get_runtime_state` (PIE).
- Not supported: authoring new tasks/conditions/evaluators/global tasks, parameter bag editing, general property binding editing, schema-specific node authoring, or porting Blueprint logic into native code.

If a request requires unsupported node or binding authoring, report that the MCP surface does not support it yet and suggest a manual editor step or a future feature request.

## Exit Contract

When finishing, always report:

- **Status:** completed | blocked | partial
- **Summary:** what was done
- **Validation:** check_structure result and compile result when run
- **Artifacts:** asset paths created or modified
- **Fingerprint:** latest fingerprint for changed assets
