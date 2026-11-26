---
name: cortex-animation
description: Use when inspecting skeletal animation assets or Animation Blueprint bindings and graphs, or for capability-gated authoring of named notifies, curves, sections, sockets, object notifies, notify states, and AnimBP function rebinding through UnrealCortex.
---

# Cortex Animation

Work with Unreal skeletal animation assets through the `anim` MCP domain.

## Before Using Tools

1. Read `.cortex/domains/anim.md` if present.
2. Prefer `anim_cmd(command="...", params={...})` and use exact command names from live capabilities.
3. Inspect first and use the returned shared Cortex `fingerprint` as `expected_fingerprint` before any mutation.

## Supported Surface

Inspection:

- `list_assets`
- `get_sequence_info`
- `get_montage_info`
- `get_skeleton_info`
- `get_animbp_info` (state machines, states, conduits, transitions with `graph_guid`; opt-in `include`: `bindings`, `node_functions`, `property_access`, `lifecycle`, `notify_handlers`; limits `state_machine_limit`, `state_limit`, `conduit_limit`, `transition_limit`, `binding_limit`)

Authoring is intentionally narrow and capability-gated:

- `add_named_notify`
- `update_named_notify`
- `remove_named_notify`
- `add_curve`
- `set_curve_keys`
- `remove_curve`
- `add_montage_section`
- `update_montage_section`
- `remove_montage_section`
- `add_socket`
- `set_socket_transform`
- `remove_socket`
- `add_notify`, `update_notify`, `remove_notify`
- `add_notify_state`, `update_notify_state`, `remove_notify_state`
- `rebind_function` (AnimBP function bindings and the three function slots; `dry_run` defaults to **true**)

Named notify mutations apply only to zero-duration sequence skeleton named notifies. Float curves, object notifies, and notify states apply to `UAnimSequence`; montage sections apply to `UAnimMontage`; sockets apply to `USkeleton`. Object-notify selectors use `{ index, class_path, time }`; state selectors also include `duration`. All mutations require `asset_path`, a precise input or selector, and `expected_fingerprint`; they support `dry_run` and optional `save` (`false` by default). Use an authoring family only when live capabilities advertise that complete family.

## AnimGraph Node Settings (`graph_cmd`)

A node's settings (the `Node` struct of an `AnimGraphNode_*`: bone references, enum modes such as `RotationMode` or `AlphaInputType`, blend settings, arrays of structs on custom nodes) are read and written through `graph_cmd`, not `editor.run_python` text edits:

1. `get_node_settings {asset_path, graph_name:"AnimGraph", node_id}` returns `settings` (or one value with `property_path`), `pin_properties`, `target_skeleton` and a `fingerprint`.
2. `set_node_settings {asset_path, graph_name, node_id, values:{"BoneToModify.BoneName":"spine_01", "AlphaInputType":"Bool", "AlphaBoolBlend.BlendInTime":0.2}, expected_fingerprint, dry_run}`. Paths are relative to the node struct; `Name[N]` addresses an existing array element; a struct value updates only the fields it names. Preview with `dry_run:true`, then apply.
3. The write is one undo step and behaves like a details-panel edit: the node reacts and is reconstructed, so pins whose visibility changes (`bAlphaBoolEnabled` after `AlphaInputType:"Bool"`) are usable at once and `pins_added`/`pins_removed` report them; links on surviving pins are kept. Link new pins only after the write.
4. Bone names are validated against the Anim Blueprint's target skeleton (`INVALID_VALUE` for a missing bone; a template Anim Blueprint returns a warning instead). Members in `pin_properties` (exposed as a pin, or bound) are refused with `INVALID_OPERATION`: set them with `set_pin_value`. A `change` with `adjusted:true` means the node changed the value itself, as the editor would.
5. Compile and save stay explicit. Nested Anim Blueprint graphs (states, transitions) are read-only for every graph mutator.

## Property Access Nodes (`graph_cmd`)

Anim Blueprints read owner state through Property Access nodes (`K2Node_PropertyAccess`). Reading one more piece of owner state needs one more node, not a C++ base class and a reparent:

1. Read: `get_subgraph` / `search_nodes {node_class:"K2Node_PropertyAccess"}` return `property_access: {path, text_path, resolved, thread_safe}` on each such node. `thread_safe` describes the path (a non-thread-safe path is copied on the game thread into a cached variable at compile); with `resolved:false` it means unknown.
2. Author: `add_node {node_class:"PropertyAccess", params:{path:["GetOwningActor","bHidden"]}}`, or a `PropertyAccess` node in `apply_patch` with the same `params.path`. Segments are properties (`Name[N]` for an array element) or getter functions (one return value, no parameters), resolved from the Anim Blueprint's class: compile first after adding a member variable the path reads. `describe_node {node_class:"PropertyAccess", asset_path, params:{path}}` previews the typed `Value` pin.
3. Refused: non-Anim and child Anim Blueprints and macro graphs (`INVALID_OPERATION`); a segment that does not resolve (the message names it), an index on a getter or a non-array, and members denied by the editor permission lists (`INVALID_FIELD`). The node is created with the Automatic call site; changing an existing node's path is not supported (remove it and add a new one).

## AnimBP Migration To A Native `UAnimInstance`

Nested graphs (state machine, state, transition rule, custom transition, conduit, blend space) are read with `graph_cmd`: `list_graphs` with `include_subgraphs:true`, then `get_subgraph` by `graph_guid` (or `graph_path` when `graph_guid_unique` is false or a repeated name such as `Transition` collides). They are read-only.

1. `get_animbp_info` with `include:["bindings","node_functions","property_access","lifecycle","notify_handlers"]`: which Blueprint members anim nodes read (`root_declared_in:"blueprint"`), which functions the slots/bindings name, which update hooks exist and which calls are not thread-safe (what a native `NativeThreadSafeUpdateAnimation` must avoid), and which `AnimNotify_*` handlers a native handler could replace (`native_signature_compatible`, `conflict`). `unsupported_binding_nodes` or a truncation marker means the analysis is incomplete, not empty.
2. Variables: `blueprint_cmd adopt_native_member` (retargets anim bindings and property-access nodes while the Blueprint variable still exists), never `remove_variable` first. Re-run `get_animbp_info`: same binding count, `root_declared_in:"native"`.
3. Functions: `rebind_function {asset_path, from, to, expected_fingerprint, dry_run}`: dry run lists `would_retarget` and `unmodified_references` (K2 call nodes are never touched; a same-named function of another class is listed `different_owner`), then apply (`compile` defaults to true, `save` to false). Rebind while the old function still exists, then retire the old function with the guarded `blueprint_cmd remove_graph` (preview with `dry_run:true` first); `remove_variable` is for variables only. A failure restores the captured state and runs one recovery compile; `rollback_status:"verification_failed"` / `VERIFICATION_FAILED` means the asset is blocked until the editor restarts: stop and report.
4. Notify handlers are mapping and readiness only: `notify_handlers` reports `native_declares`, `native_signature_compatible` and `conflict` (a native `AnimNotify_<Name>` makes the Blueprint event fail to compile). Guarded removal of an ordinary editor-created `AnimNotify_*` event entry is currently unavailable (`retire_entries` refuses non-override events; `prune_island` keeps the entry; open request `docs/requests/graph/2026-11-05-graph-policy-driven-reviewed-removal-node-families.md`). Report the conflict instead of adding the native handler to a shipped AnimBP, and never remove the event by other Cortex commands.

## Guardrails

- Use `dry_run=true` before destructive or uncertain changes.
- Treat stale fingerprint errors as a signal to re-inspect and ask whether to retry.
- Do not invent later-stage AnimBP authoring, blendspace, retargeting, runtime preview, Sequencer, or Control Rig commands. The only anim-domain AnimBP mutation is `rebind_function`; anim node settings are written with `graph_cmd set_node_settings` (above), bindings and logic are not editable here and nothing ports Blueprint logic to C++. The anim domain has no save command; use a mutation's `save=true` option, or `core.save_asset` where appropriate.
- If a command is absent from live capabilities, report that the requested animation authoring is unavailable.

## Verification

For C++ domain changes, run:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "& { Set-Location 'cli/Testing'; .\RunTests.ps1 'Cortex.Animation+' }"
```

For MCP scenario coverage with an editor running:

```bash
cd Plugins/UnrealCortex/MCP && uv run pytest tests/test_mcp_scenarios.py -v -k animation
```
