# Typed Blueprint Authoring

Single workflow reference for constructing a small typed adapter on an existing Blueprint or Widget
Blueprint: discover live, describe, preview, apply under a guard, verify by readback, persist only on
explicit authority. Routed here by `skills/cortex-blueprint`, `skills/cortex-umg` and
`skills/cortex-bp-migrate`.

This guide does not define the contract. The connected Editor owns it: `graph.get_authoring_context`,
`graph.describe_node`, `graph.apply_patch` and the profile schemas served by
`core.get_operation_schema`. Read the live schema before you build a request, and treat the values
published there as authoritative for field names, defaults, limits, families and errors.

## Live contract

Obtain `core.get_operation_schema` for `graph.get_authoring_context`, `graph.describe_node` and
`graph.apply_patch` through the connected Editor. Respect the selected facade profile: the
`UMGAuthoring` profile exposes `umg`, `graph` and `core`, so the graph operations below are
reachable while unrelated Blueprint-domain commands stay blocked.

Cached metadata, a capability fixture, or a prior-session success is not live capability evidence.
A missing command, a missing profile permission or an editor that does not know `graph.apply_patch`
means **blocked**: stop, record the editor and plugin identity, and request an authorized
rebuild/reload path. Never fall back to `core_cmd(batch)` composition, to the removed legacy
`blueprint_compose` update batch, to `run_python`, or to raw describe/add/connect calls to reach the
same mutation.

`graph.apply_patch` is a standalone command: it is **not nestable inside a rollback-enabled Core
batch**, because an outer batch cannot undo its compile or its save boundary. Call it directly
through `graph_cmd(command="apply_patch", params={...})`, or through
`blueprint_compose(mode="update", asset_path=..., patch={...})`, which forwards exactly one reviewed
envelope and owns the envelope `asset_path`:

- `patch.asset_path` that conflicts with the envelope asset (including an explicit `null`) is
  refused before forwarding with `INVALID_PATCH`.
- Legacy update fields supplied next to `patch` are refused as a mixed contract
  (`MIXED_UPDATE_CONTRACT`); the stale-write guard belongs inside `patch.expected_fingerprint`.
- `mode="update"` without `patch` fails with `MIGRATION_REQUIRED` and the message
  "mode='update' requires a 'patch' object". The legacy batch update route was removed and is never
  used as a fallback.

Create mode is a separate, unchanged route; this guide covers updates to existing assets.

### Refusal codes

| Code | Raised when |
|---|---|
| `MIGRATION_REQUIRED` | `mode="update"` arrived without a `patch` object (the removed legacy route is never a fallback). |
| `MIXED_UPDATE_CONTRACT` | Legacy update fields were supplied beside `patch`. |
| `INVALID_PATCH` | The facade rejects the patch's own shape: a conflicting `patch.asset_path`, a non-object or empty `patch`, or a flag that is not a JSON boolean. |
| `INVALID_FIELD` | Native shape validation: an unknown field, a malformed flag type (a boolean is never coerced), a missing required selector, an unmapped reference, a `replace_entry` parent-call target. |
| `STALE_PRECONDITION` | The fingerprint or the preview token no longer matches the live state; nothing was mutated. |
| `DIRTY_EDITOR_STATE` | `save=true` against a package that is not clean. |
| `LIMIT_EXCEEDED` | The request or the scanned state exceeds a published bound. |
| `PIN_TYPE_MISMATCH` | A boundary mapping is type-incompatible or targets an expanded (struct-split) pin. |
| `INVALID_OPERATION` | The asset or graph state cannot carry the request: an unverified-rollback block, a cross-graph duplicate identity, a graph that is not the target declaration's graph, a prune entry identity owned by several graphs. |
| `UNSUPPORTED_OPERATION` | An unknown `migration.op`; only the published operations are accepted. |

### Envelope

The native envelope (all fields published by the live schema):

| Field | Notes |
|---|---|
| `asset_path` | Full asset path; the request must name the same asset the facade forwards. |
| `target` | Locator: `graph_ref` with a canonical `graph_guid` (plus optional `subgraph_path`), or `implementation` with `owner_class` + `function_name`. Required by the authoring shell and by `replace_entry`; must be **absent** for `copy_subgraph` / `move_subgraph` / `prune_island`, which address their graphs inside `migration`. |
| `patch_id` | Caller-generated UUID that deterministically derives the identity of every new node. Reuse it for an idempotent repeat, never for a different mutation set. |
| `expected_fingerprint` | Stale-write guard copied from `graph.get_authoring_context`. Never fabricate or reuse a fingerprint across edits. |
| `nodes`, `connections`, `pin_updates` | The authoring shell. One family identifier per node, tagged defaults, structured edges. |
| `migration` | The migration shell: exactly one operation per request. Never mixed with a non-empty authoring array. |
| `dry_run` | Preview only. Default `true`. |
| `compile` | Compile the target once after a reversible apply. Default `true`. |
| `save` | Persist after verified readback. Default `false`. |
| `allow_noop` | Permit an explicitly change-free patch instead of refusing it. Default `false`. |
| `expected_validation_hash` | Preview token; required when `dry_run=false`. |

Booleans are strict JSON booleans and are **never coerced**: `1`, `"true"` and `"false"` fail with
`INVALID_FIELD` instead of silently selecting a default. Unknown fields fail too — there is no
lenient path.

The Editor publishes its own bounds (`graph.get_authoring_context` → `limits`, and the same bound
descriptions on the `graph.apply_patch` schema: node, edge, client-id, request-size and scan
budgets). Read them live; this guide does not restate numbers that the contract can change.

### Discovery before a request

1. `graph.get_authoring_context` for the asset: candidate graphs (with canonical GUIDs, kind,
   mutability, subgraph paths), the current fingerprint, and the published families. Note that its
   `target` parameter currently resolves only `graph_ref`: asking it to resolve an `implementation`
   target fails with `UNSUPPORTED_OPERATION`, so take the fingerprint without a target and supply
   `target.implementation` (`owner_class` + `function_name`) from the declaration you read.
2. `graph.describe_node` for every family you intend to use. It returns the canonical class, the
   accepted construction parameters and the pins that will exist, including the pins allocated from
   a class selector or an exposed-on-spawn input. Use its names; never guess a pin, an alias or a
   selector, and never carry a private catalog of them.
3. Read the existing graph (`get_subgraph`, `search_nodes`, `find_event_handler`) to learn the exact
   node GUIDs, pin names and current links you will connect to or update.

Outputs and event parameters are **edges**, not defaults. A structured endpoint must be wired: create
(or reuse) a `Self` node and wire its output to the create node's outer input — the input Blueprint
displays as `Outer`, whose addressable name `graph.describe_node` publishes is `self`. Address every
pin by the `PinName` describe publishes, never by a display or friendly name: a `DynamicCast` result
pin is `As` plus the target's display name, and a variable node's pin is the variable name. There is
no `$self` magic object reference, and a caller-supplied object literal in `defaults` in place of an
edge is refused rather than coerced. Tagged defaults are for unconnected input pins only; a default
and an edge on the same input, a default on an output pin, a kind that contradicts the pin's native
storage mode and an unresolvable class/object path all fail preflight.

## Preview

1. Inspect the exact asset and the exact graph or implementation target.
2. Build the intent from live canonical selectors and tags: `client_id` (1–32 ASCII letters, digits,
   `_` or `-`; `entry` is reserved), `node_class`, `params`, tagged `defaults` and optional
   `position`; `connections` whose `from`/`to` carry exactly one identity (`client_id`, `node_guid`,
   or `entry: true` for the implementation entry) plus `pin`.
3. Obtain the fingerprint and send the intent with `dry_run=true`, `compile=true`, `save=false`.
4. Keep `patch_id`, the returned `node_mappings`, `validation_hash` and the previewed intent
   together. The token is a precondition derived from the normalized intent, the fingerprint, the
   resolved symbols and the schema context — not an authentication secret, and not reusable after
   the state changes.

A preview never mutates, never compiles and never saves. It reports `changed`, `apply_status`/
`compile_status`/`readback_status`/`rollback_status`/`save_status` as `not_requested`, the live
before/after fingerprint and dirty state, the planned `locators`, and every planned or reused
identity in `node_mappings` (`reused_client_ids` names the deterministic nodes it would reuse).

A migration preview publishes its bounded inventory so you never have to read a private plan:
transfers publish `crossing_edges`, `boundary`, `dependencies`, `removal_set`, `internal_edges`,
`node_count` and both graph GUIDs; `prune_island` publishes a partition (`removable`, `shared`,
`blocked`, `external_edges`, `complete`, scan counts). Like diagnostics, the informational lists are
bounded and carry a single omission marker; the `removable` set is published complete because you
must echo it exactly.

`replayed_with_absent_source` is published on preview and apply. It is `true` when the source
locator you named no longer exists and the request was accepted as an idempotent replay of work this
patch id already performed; the response carries a diagnostic saying so. Absence alone never proves
that a destructive operation succeeded — read the current state before concluding anything.

## Apply

1. Require user/task authority for the exact mutation set before sending it.
2. Send the **same** intent with `dry_run=false` and `expected_validation_hash` from the preview.
   Keep `save=false` unless you have explicit persistence authority.
3. Compile once for a changed patch (the default), then inspect the canonical readback instead of
   assuming success.
4. Report the outcome by phase.

A stale fingerprint or a stale token fails `STALE_PRECONDITION` before any mutation. An identical
repeat reports `apply_status="unchanged"` and performs no compile, no save, no layout change and no
new undo entry. A partial or conflicting deterministic identity set is refused outright — not
completed, not repaired. Read the result by phase:

| Field | Meaning |
|---|---|
| `apply_status` | `applied`, `unchanged` or `failed`. |
| `compile_status` | `compiled`, `failed` or `not_requested` (an apply with `compile=false` never claims compile success). |
| `readback_status` | `matched` or `mismatched` — canonical identity comparison, never display text. |
| `rollback_status` | `restored` (exact restoration verified) or `unverified`. |
| `save_status` / `post_save_status` | `not_requested`, `saved`, `failed` / `verified`, `failed`. |
| `target_compile_count`, `recovery_compile_count` | Compiles actually performed. |
| `saved`, `blocked` | Persistence result and the blocked-for-mutation state. |
| `locators`, `node_mappings` | Durable identities to re-resolve, never transient pointers. |
| `fingerprint_before` / `fingerprint_after`, `dirty_before` / `dirty_after` | Live state around the patch. |
| `diagnostics` | Bounded (16 entries, 512 characters each, single omission marker). |

Read back through reads (`get_subgraph`, `search_nodes`, `blueprint_cmd(get_info)`) and compare the
canonical identities and tagged defaults the patch mapped, not the visual layout.

## Persistence

`save=true` is an explicit, separate disk boundary and the only step that persists. It requires
`compile=true` and a clean starting package; a dirty starting package is refused
(`DIRTY_EDITOR_STATE`) rather than silently persisting unrelated work. Persistence happens only after
a verified readback, so a successful compile is not a successful save and a preview never saves.

`save=true` commits the file and is never rolled back: if the save fails after a verified apply,
report an applied-but-unsaved state instead of replaying the graph mutation. `save=false` preserves
unrelated unsaved work in an already-dirty package.

A designer widget that is not a variable cannot be read or written by the graph patch. Repair it as a
**separate** `umg.set_widget_variable` operation, then refresh the context and obtain a fresh
fingerprint — the widget-variable repair is its own operation and is never part of the patch
transaction, and the pre-repair fingerprint must never be reused.

## Recovery

No blind retry. After a timeout, a lost response, save uncertainty, a stale guard or an unverified
rollback, read the current state first, reconcile the identities you already have, and re-preview
before sending anything again. A retried mutation with a stale guard or a new identity is how a
small failure becomes a duplicated graph.

The patch journals its own changes and reverses them exactly on a late failure. When restoration is
verified the result reports `rollback_status="restored"` and the asset stays usable. When it cannot
be verified the asset is **blocked from mutation** (`rollback_status="unverified"`, `blocked=true`)
and later graph mutations are refused with `INVALID_OPERATION` — plus a reason. Preserve the residual
diagnostics and escalate; do not restart, reload, save or clean the package to make the block go
away, and do not treat a blocked asset as successfully reverted.

Always report the original structured error together with the phase statuses. Never report a failed
phase, a dirty package or an unverified rollback as success.

## Migration operations (supported subset)

One operation per request, inside `migration`, never mixed with the authoring shell. Selectors and
identities come from the live context and reads; the shapes below are the contract, not a substitute
for `describe_node` and the schema.

**`replace_entry`** — replace a stale inherited implementation entry while preserving the downstream
body:

```json
{"op":"replace_entry",
 "source":{"graph_ref":{"graph_guid":"…"},"entry_node_guid":"…"},
 "pin_map":[{"entry":"input","from_pin":"…","to_pin":"…"}],
 "remove_shadowing_member":false}
```

It requires `target.implementation` (`owner_class`, `function_name`), refuses a `call_kind="parent"`
target (`replace_entry` preserves the body and never authors a parent call), and removes a shadowing
Blueprint variable only when `remove_shadowing_member=true` and the reference set is provably
interior to the asset. Every visible pin of the replacement terminator must be mapped exactly once.

**`copy_subgraph` / `move_subgraph`** — bounded same-asset transfer of a selected node set between
two graphs, with an explicit boundary mapping for every crossing edge:

```json
{"op":"copy_subgraph",
 "source":{"graph_ref":{"graph_guid":"…"},"node_guids":["…"]},
 "destination":{"graph_ref":{"graph_guid":"…"}},
 "boundary":[{"from":{"node_guid":"…","pin":"…"},"to":{"node_guid":"…","pin":"…"}}]}
```

`target` must be absent. A crossing edge needs exactly one boundary entry; an expanded (struct-split)
destination pin, an incompatible pin type, a destination that already owns the planned identity in
another graph, or a partial selection (neither a fresh transfer nor a complete replay) is refused.
`move_subgraph` needs a destination graph different from the source.

**`prune_island`** — remove only the uniquely owned execution island of one entry:

```json
{"op":"prune_island",
 "source":{"graph_ref":{"graph_guid":"…"},"entry_node_guid":"…"},
 "approved_node_guids":["…"]}
```

Preview without `approved_node_guids` publishes the partition; apply echoes exactly the `removable`
set you approved (`awaiting_approval` flips on the apply, `reused` marks an idempotent replay).
`complete=false` means the scan budget was exhausted — it never means "empty island". Never send an
empty approved set, and never substitute disconnect-plus-orphan-deletion for ownership-aware
pruning: a node the entry does not uniquely own is `shared` or `blocked` and stays.

## When something is wrong

| Situation | Required next action |
|---|---|
| Live command absent | Stop, record editor/plugin identity, request an authorized rebuild/reload path; no fallback mutation. |
| Designer widget not variable | Isolated guarded UMG repair, then fresh context/preview. |
| Static validation error | Correct only from the returned canonical contract; respect the facade retry budget. |
| Stale fingerprint/token | Inspect changed state and re-preview; do not overwrite. |
| Partial/conflicting deterministic IDs | Reconcile the existing graph; do not append or delete to force a match. |
| Compile/readback failure, rollback verified | Report failure and restored state; no save. |
| Rollback unverified | Stop writes; preserve residual detail and escalate. |
| Save failed after verified apply | Report applied-but-unsaved state; do not replay graph mutation. |
| Lost response | Read current state first; an absent source alone does not prove a destructive operation succeeded. |

## Examples

`examples/typed-blueprint-authoring/` holds executable JSON intent fixtures with their live-bindings
table: the authoring preview/apply pair, `replace_entry`, `copy_subgraph`, `move_subgraph` with
explicit boundary mappings, `prune_island` preview plus approved-set apply, and the negative requests
that must be refused. Every fixture states which parts are bound live; none of them contains a
fingerprint, a validation token or a fabricated GUID.
