# Typed Blueprint Authoring — intent fixtures

Executable **intent** fragments for `graph.apply_patch`, described by
`resources/typed-blueprint-authoring.md`. None of these files is a complete request: the live
harness supplies the envelope fields that only the Editor can know, and the fragments never carry a
fabricated fingerprint, validation token, GUID or pin that the live contract must decide.

Validation: `python -m unittest discover -s tests -p 'test_typed_blueprint_authoring_guidance.py' -v`
from the toolkit root. Those checks prove guidance and JSON *shape* only; they do not prove Unreal
behaviour, and they deliberately carry **no** catalog of families, operations, default tags, limits or
selectors. A value the check does not know about is not rejected by it: families and selectors are
**accepted live** by `graph.describe_node` and the native preflight, migration operations by the
planner, tags by the native pin-defaults owner, and limits by
`graph.get_authoring_context`. The live bindings these fixtures name are exercised by the consuming
plugin scenario under an Editor lease.

## Conventions

- A fragment contains **only** envelope fields (`target`, `nodes`, `connections`, `pin_updates`,
  `migration`, the flag fields and the apply-only `expected_validation_hash`). Nothing else is added,
  so a fragment can be lifted into a request without translation.
- Every value the run must supply is written as a `<live: …>` token. A token is never a real value:
  there is no GUID, no hash and no token literal in these files, and every token below is declared.
- Names the fixture itself declares (the designer widget variable, the Blueprint variable, the
  recording function, the entry's parameter, the native fixture base class) are written literally and
  are listed as fixture-owned, so a live mismatch is a fixture change, not a guess.
- Pin names follow the engine's addressable `PinName`, which is what `graph.describe_node` returns
  and what the patch resolves: `execute`, `then`, `self` (a Self node's output **and** the create
  node's outer input, whose Blueprint-facing friendly name is `Outer`), `Object` (a cast's input),
  `ReturnValue`. A pin allocated from a class selector is a token, because its name is derived from
  the class at allocation time.
- Envelope fields the harness always adds and no fragment carries: `asset_path`, `patch_id` (a fresh
  UUID per mutation set), `expected_fingerprint` (from `graph.get_authoring_context`), and `target`
  unless the fragment shows it.

## Files

| Fixture | Shell | Purpose |
|---|---|---|
| `adapter-intent.json` | authoring | Preview of the generic `PresentTitle` adapter. |
| `adapter-apply.json` | overlay | The apply step of that preview: `dry_run=false` plus the preview token. |
| `replace-entry-intent.json` | migration | Preview of `replace_entry` on the stale inherited `PresentTitle` entry. |
| `copy-subgraph-intent.json` | migration | Preview of `copy_subgraph` with one explicit boundary mapping. |
| `move-subgraph-intent.json` | migration | Preview of `move_subgraph`, same selection and boundary shape, different destination graph. |
| `prune-island-intent.json` | migration | Preview of `prune_island`: the partition, no approved set. |
| `prune-island-apply.json` | migration | The apply overlay: the approved `removable` set and a token from a fresh preview of that exact approved intent. The bounded MCP route accepts only complete previews within its response budget. |
| `negative/*.json` | descriptor | Requests that must be refused, with the code, the message fragment and where the refusal is enforced. |

Every migration fixture is a preview (`dry_run=true`) except `prune-island-apply.json`. The apply
step of every other fragment is the same intent with `dry_run=false` and
`expected_validation_hash` from the preview, exactly as `adapter-apply.json` shows; nothing else
changes between preview and apply.

## Live bindings

**Run scope**

| Token | Binds to | Supplied by |
|---|---|---|
| `<live: run>` | The run label of the declared asset root `/Game/Temp/CortexGraphAuthoring_<run>/` (the T15 brief spells it `<run>`). | The scenario's declared run root. |
| `<live: asset_path>` | The asset under authoring. | The scenario fixture. |
| `<live: the reviewed graph.apply_patch envelope>` | The one envelope the facade forwards. | The checked-in fragments in this directory. |

**Identity from context and reads**

| Token | Binds to | Supplied by |
|---|---|---|
| `<live: source graph_guid>` | The graph the request mutates (`graph_ref.graph_guid`). | `graph.get_authoring_context`. |
| `<live: destination graph_guid>` | The second graph of a transfer, or the graph of a negative case. | `list_graphs` / a candidate read. |
| `<live: selected node GUID>` | A node of the selected set. | A graph read. |
| `<live: first selected node GUID>` | The first node of a two-node selection. | A graph read. |
| `<live: second selected node GUID>` | The second node of the same selection. | A graph read. |
| `<live: selected source node GUID>` | The selected node one crossing edge leaves. | A graph read. |
| `<live: existing destination node GUID>` | The destination-side node a boundary mapping targets. | A destination graph read. |
| `<live: destination node GUID>` | A destination-side node named by a boundary mapping or a negative case. | A destination graph read. |
| `<live: stale entry node_guid>` | The stale entry `replace_entry` replaces. | A graph read. |
| `<live: island entry node_guid>` | The entry whose uniquely owned island `prune_island` removes. | A graph read. |
| `<live: legacy node spec>` | A legacy batch node specification, used only by a refused facade call. | The negative case's author. |
| `<live: legacy connection spec>` | A legacy batch connection specification, used only by a refused facade call. | The negative case's author. |

**Pins from `graph.describe_node` and reads**

| Token | Binds to | Supplied by |
|---|---|---|
| `<live: cast target display name>` | The display name half of a `DynamicCast` result pin; the engine names that pin `PN_CastedValuePrefix + <target display name>` (prefix `As`). | `graph.describe_node` for the cast node. |
| `<live: stale entry output pin>` | An output pin of the stale entry. | `graph.describe_node` / a read. |
| `<live: replacement entry output pin>` | The replacement entry's pin the stale output is re-wired to. | `graph.describe_node` for the implementation target. |
| `<live: crossing source pin name>` | The selected-side pin of a crossing edge. | `graph.describe_node` / a read. |
| `<live: destination pin name>` | The destination-side pin that edge is mapped to. | `graph.describe_node` / a read. |
| `<live: struct-expanded destination pin>` | A destination pin whose struct is split, which the transfer cannot prove. | A read of an expanded pin in the negative scenario. |

**Values returned by a preview**

| Token | Binds to | Supplied by |
|---|---|---|
| `<live: validation_hash returned by the preview>` | The token required by an apply. | The `dry_run=true` response. |
| `<live: a token from a preview of an earlier state>` | A deliberately stale token, used only by the negative case. | An earlier preview. |
| `<live: removable set published by the preview>` | The `removable` list the caller approves. | The `prune_island` preview response — only when that response arrived complete; a truncated or oversized preview is not approvable. |

## `adapter-intent.json` — authoring preview

The generic adapter for `PresentTitle(FText)` on a Widget Blueprint: read the designer widget, cast
it to its generated class, construct the model, call the Blueprint-defined recording function on the
cast result, and keep the model in a Blueprint variable.

| Node | Family | Fixture-owned selector |
|---|---|---|
| `self` | `Self` | — |
| `title_label` | `VariableGet` | `TitleLabel` — the designer widget variable. It must already be a variable (a separate `umg.set_widget_variable` repair; never part of the patch transaction). |
| `host_cast` | `DynamicCast` | `is_pure: false`, so the cast has an execution path and its failure path can be routed. The cast class is the designer widget's generated class. |
| `model` | `ConstructObject` | The generated model class; `Title` is its inherited exposed-on-spawn FText input. |
| `record` | `CallFunction` | `RecordObservedTitle` on the same generated class. |
| `store_model` | `VariableSet` | `ModelRef` — a Blueprint variable on the authored asset (self-context, so its target is not wired). |

| Edge | Why it exists |
|---|---|
| `entry.then → model.execute`, `model.then → host_cast.execute`, `host_cast.then → record.execute`, `record.then → store_model.execute` | One execution chain from the implementation entry. |
| `self.self → model.self` | Self→Outer: the constructed object's outer is an explicitly wired `Self` node. There is no `$self` object literal, and a caller-supplied `{"node": "…"}` default is not accepted. |
| `entry.Title → model.Title` | The implementation entry's `Title` parameter feeds the model's exposed-on-spawn input. |
| `title_label.TitleLabel → host_cast.Object` | The designer widget read is what the cast checks. |
| `host_cast.As… → record.self` | The cast result is the call's **explicit** target; the call is never left to default-to-self. |
| `model.ReturnValue → record.Model` | The construction result is the function input. |
| `record.ReturnValue → store_model.ModelRef` | The model reference is stored, so the fixture owns the lifetime instead of relying on `Outer`. |

`record.defaults.Title` is a tagged text default on an unconnected input (`{"kind": "text",
"literal": …}`), which is the only shape the contract accepts for a default: a bare string, a bare
object and an edge-shaped object are refused. The literal is fixture-owned; the harness re-binds the
pin name and the literal when it binds the fixture's recording function.

The fragment carries no `target`, so the harness supplies it: the implementation target
(`{"implementation": {"owner_class": …, "function_name": "PresentTitle"}}`) for the Widget Blueprint
case, or a `graph_ref` for the Actor Blueprint case the scenario also exercises.

## `adapter-apply.json` — the apply step

An overlay of the preview fragment, not a second request: send `adapter-intent.json` with these two
values and nothing else changed, so the applied intent is provably the previewed one.

| Field | Value |
|---|---|
| `dry_run` | `false` |
| `expected_validation_hash` | `<live: validation_hash returned by the preview>` |

`save` stays `false` in both: persistence is a separate, explicitly authorized step.

## Migration fragments

- **`replace-entry-intent.json`** — the fixture's declared implementation target
  (`/Script/CortexSandbox.CortexGraphAuthoringWidgetBase.PresentTitle`), the stale entry's graph and
  GUID, and a `pin_map` mapping each mappable entry output (`OutputDelegate`, `then`, `Title`)
  exactly once (`remove_shadowing_member: false`, so a same-named Blueprint variable is reported
  rather than removed). `target` is required here.
- **`copy-subgraph-intent.json`** / **`move-subgraph-intent.json`** — a two-node selection, the
  destination graph, and one boundary mapping per crossing edge. `target` must be absent; the graphs
  are named inside `migration`. `move_subgraph` needs a destination graph different from the source.
- **`prune-island-intent.json`** — the entry whose island is measured; the preview publishes
  `removable`, `shared`, `blocked_nodes`, `external_edges`, `complete` and scan counts; `blocked`
  remains the Boolean asset-block status.
- **`prune-island-apply.json`** — the same graph and entry plus
  `approved_node_guids: [<live: removable set published by the preview>]`. Since approval changes
  the intent, preview it again with that exact set and use **that** token for the apply. An approved
  set is never empty; `complete=false` means the scan budget was exhausted, not an empty island.

The bounded complete-or-refuse MCP prune route is implemented; an oversized apply is refused before
mutation when the conservative prospective result exceeds the budget. Only lossless large-island
inventory retrieval remains unsupported and is future scope; the bounded response guard is tracked
at [CortexSandbox #102](https://github.com/etelyatn/CortexSandbox/issues/102). Details and exact
refusal fields live in [`resources/typed-blueprint-authoring.md`](../../resources/typed-blueprint-authoring.md).

`max_response_chars=40000` is the MCP response budget, while `max_scanned_nodes` bounds native
traversal; no separate prune-node cap exists. Approve only a complete delivered inventory, preview
the exact approved set again, and apply with that second preview token. `graph.apply_patch` mutation
approval is not paginated, and every `core_cmd(batch_query)` rejects it before any subcommand,
regardless of rollback settings.

After a lost, oversized or ambiguous apply outcome, **Stop and reconcile** by reading current state.
Never approve a partial set, blindly resend the mutation, or treat response readback as a
pre-mutation gate.

## Negative fixtures

Each descriptor names the request, the code, a message fragment, and where the refusal is enforced.
Codes appear in the guide's refusal table; the checks assert that traceability.

| Case | Surface | Code | Enforced by |
|---|---|---|---|
| `update-without-patch` | facade | `MIGRATION_REQUIRED` | Plugin facade test `test_update_without_patch_reports_migration_error_and_never_calls_editor`. |
| `mixed-legacy-update-fields-with-patch` | facade | `MIXED_UPDATE_CONTRACT` | Plugin facade test `test_update_mixed_legacy_fields_with_patch_fail_locally`. |
| `coerced-boolean-flag` | facade | `INVALID_PATCH` | Plugin facade test `test_update_rejects_non_boolean_patch_flags_locally` (flags are never coerced). |
| `unsupported-migration-op` | native | `UNSUPPORTED_OPERATION` | Native migration planner: only the published operations are accepted. |

**Bound live (`live_only: true`)** — these cases only exist against real state, so nothing in this
repository can prove them; they are declared here and must be exercised by the consuming scenario
under an Editor lease.

| Case | Surface | Code | Live condition |
|---|---|---|---|
| `stale-validation-token` | native | `STALE_PRECONDITION` | The token comes from a preview of an earlier state; nothing is mutated. |
| `expanded-boundary-pin` | native | `TYPE_MISMATCH` | The destination pin is struct-expanded, which the transfer cannot prove. |
| `cross-graph-duplicate-identity` | native | `INVALID_OPERATION` | The planned destination identity is already owned by another graph. |
| `parent-call-replace-entry` | native | `INVALID_OPERATION` | `call_kind=parent` on `PresentTitle` is refused because it is not a native event; `replace_entry` never authors that parent call. |

## Expected phases

| Step | Expected result |
|---|---|
| Preview | `changed=true`, every phase status `not_requested`, a `validation_hash`, `node_mappings` for all six client ids, `locators` for the target, and an unchanged fingerprint/dirty state. |
| Apply | `apply_status=applied`, `compile_status=compiled` (one target compile), `readback_status=matched`, `save_status=not_requested`, `dirty_after=true`, `blocked=false`. |
| Repeat with the same `patch_id` | `apply_status=unchanged`, `reused_client_ids` naming the existing nodes, no compile, no save. |
| Migration preview | The bounded inventory above, exactly as published, when the response fits the MCP budget: transfers report `crossing_edges`/`boundary`/`dependencies`/`removal_set`/`internal_edges`/`node_count`; prune reports its partition and scan counts. A truncated or oversized prune response is the unsupported large-island case above: reconcile it, never approve part of it. |
| Accepted replay | `replayed_with_absent_source=true` with a diagnostic on preview and apply when the named source locator is already gone. |

## Bound live (not proven by the toolkit checks)

These need the Editor and belong to the consuming scenario: the canonical class/member selectors and
pin names, the fingerprint and preview token, the deterministic identity mapping, the tagged-default
readback, the cast-failure/null route, every phase status above, and every `live_only` negative case.
A fixture mismatch found there is a fixture correction, never a workaround in the guidance.
