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

## AnimBP Migration To A Native `UAnimInstance`

Nested graphs (state machine, state, transition rule, custom transition, conduit, blend space) are read with `graph_cmd`: `list_graphs` with `include_subgraphs:true`, then `get_subgraph` by `graph_guid` (or `graph_path` when `graph_guid_unique` is false or a repeated name such as `Transition` collides). They are read-only.

1. `get_animbp_info` with `include:["bindings","node_functions","property_access","lifecycle","notify_handlers"]`: which Blueprint members anim nodes read (`root_declared_in:"blueprint"`), which functions the slots/bindings name, which update hooks exist and which calls are not thread-safe (what a native `NativeThreadSafeUpdateAnimation` must avoid), and which `AnimNotify_*` handlers a native handler could replace (`native_signature_compatible`, `conflict`). `unsupported_binding_nodes` or a truncation marker means the analysis is incomplete, not empty.
2. Variables: `blueprint_cmd adopt_native_member` (retargets anim bindings and property-access nodes while the Blueprint variable still exists), never `remove_variable` first. Re-run `get_animbp_info`: same binding count, `root_declared_in:"native"`.
3. Functions: `rebind_function {asset_path, from, to, expected_fingerprint, dry_run}`: dry run lists `would_retarget` and `unmodified_references` (K2 call nodes are never touched; a same-named function of another class is listed `different_owner`), then apply (`compile` defaults to true, `save` to false). Rebind while the old function still exists, then retire the old function with the guarded `blueprint_cmd remove_graph` (preview with `dry_run:true` first); `remove_variable` is for variables only. A failure restores the captured state and runs one recovery compile; `rollback_status:"verification_failed"` / `VERIFICATION_FAILED` means the asset is blocked until the editor restarts: stop and report.
4. Notify handlers are mapping and readiness only: `notify_handlers` reports `native_declares`, `native_signature_compatible` and `conflict` (a native `AnimNotify_<Name>` makes the Blueprint event fail to compile). Guarded removal of an ordinary editor-created `AnimNotify_*` event entry is currently unavailable (`retire_entries` refuses non-override events; `prune_island` keeps the entry; open request `docs/requests/graph/2026-11-05-graph-policy-driven-reviewed-removal-node-families.md`). Report the conflict instead of adding the native handler to a shipped AnimBP, and never remove the event by other Cortex commands.

## Guardrails

- Use `dry_run=true` before destructive or uncertain changes.
- Treat stale fingerprint errors as a signal to re-inspect and ask whether to retry.
- Do not invent later-stage AnimBP authoring, blendspace, retargeting, runtime preview, Sequencer, or Control Rig commands. The only AnimBP mutation is `rebind_function`; bindings, graphs and logic are not editable here and nothing ports Blueprint logic to C++. The anim domain has no save command; use a mutation's `save=true` option, or `core.save_asset` where appropriate.
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
