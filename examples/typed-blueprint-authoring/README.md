# Typed Blueprint Authoring — intent fixtures

Executable **intent** fragments for `graph.apply_patch`, described by
`resources/typed-blueprint-authoring.md`. None of these files is a complete request: the live
harness supplies the envelope fields that only the Editor can know, and the fragments never carry a
fabricated fingerprint, validation token, GUID or pin that the live contract must decide.

Validation: `python -m unittest discover -s tests -p 'test_typed_blueprint_authoring_guidance.py' -v`
from the toolkit root. Those checks prove guidance and JSON shape only; they do not prove Unreal
behaviour. The live bindings they name are exercised by the consuming plugin scenario under an
Editor lease.

## Conventions

- A fragment contains **only** envelope fields (`target`, `nodes`, `connections`, `pin_updates`,
  `migration`, the flag fields and the apply-only `expected_validation_hash`). Nothing else is
  added, so a fragment can be lifted into a request without translation.
- Every value the run must supply is written as a `<live: …>` token. A token is never a real value:
  there is no GUID, no hash and no token literal in these files.
- Names that the fixture itself declares (the designer widget variable, the Blueprint variable, the
  recording function, the entry's parameter) are written literally and are listed below as
  fixture-owned, so a live mismatch is a fixture change, not a guess.
- Pin names follow the engine's addressable `PinName`, which is what `graph.describe_node` returns
  and what the patch resolves: `execute`, `then`, `self` (a Self node's output **and** the create
  node's outer input, whose Blueprint-facing friendly name is `Outer`), `Object` (a cast's input),
  `ReturnValue`. A pin allocated from a class selector is written as a token because its name is
  derived from the class at allocation time.

## Live bindings

| Token | Binds to | Supplied by |
|---|---|---|
| `<live: run>` | The run label of the declared asset root `/Game/Temp/CortexGraphAuthoring_<run>/` (the T15 brief spells it `<run>`). | The scenario's declared run root. |
| `<live: cast target display name>` | The display name half of a `DynamicCast` result pin. The engine names that pin `PN_CastedValuePrefix + <target display name>` (prefix `As`), so it cannot be checked in. | `graph.describe_node` for the cast node. |
| `<live: validation_hash returned by the preview>` | The preview token. | The `dry_run=true` response. |

Envelope fields the harness always adds and no fragment carries: `asset_path`, `patch_id` (a fresh
UUID per mutation set), `expected_fingerprint` (from `graph.get_authoring_context`), and `target`
unless the fragment shows it.

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

## Expected phases

| Step | Expected result |
|---|---|
| Preview | `changed=true`, every phase status `not_requested`, a `validation_hash`, `node_mappings` for all six client ids, `locators` for the target, and an unchanged fingerprint/dirty state. |
| Apply | `apply_status=applied`, `compile_status=compiled` (one target compile), `readback_status=matched`, `save_status=not_requested`, `dirty_after=true`, `blocked=false`. |
| Repeat with the same `patch_id` | `apply_status=unchanged`, `reused_client_ids` naming the existing nodes, no compile, no save. |

## Bound live (not proven by the toolkit checks)

These need the Editor and belong to the consuming scenario: the canonical class/member selectors and
pin names, the fingerprint and preview token, the deterministic identity mapping, the tagged-default
readback, the cast-failure/null route, and every phase status above. A fixture mismatch found there
is a fixture correction, never a workaround in the guidance.
