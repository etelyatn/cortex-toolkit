# Safe Graph Authoring Toolkit Sync

## Purpose

Synchronize Cortex Toolkit guidance with UnrealCortex safe graph authoring recovery
without adding a parallel recovery guide.

## Scope

Update the existing documentation agents already use:

- `resources/mcp-tool-reference.md` lists `graph.describe_node` and
  `umg.set_widget_variable`, and explains `core.batch_query` rollback controls.
- `skills/cortex-blueprint/SKILL.md` requires inspecting a node contract before a
  raw `graph.add_node` mutation.
- `skills/cortex-umg/SKILL.md` documents fingerprint-guarded
  `set_widget_variable` mutations on existing Widget Blueprints.

## Behavior

Graph authors inspect the target graph/node contract with `graph.describe_node`
before calling raw `graph.add_node`, then use the returned pin and parameter
contract to construct the request. Invalid requests are corrected before a
mutation is sent.

UMG authors use `umg.set_widget_variable` only after inspecting the current
Widget Blueprint state and pass its `expected_fingerprint`. New widget screens
continue to use `widget_compose`.

`core.batch_query` accepts `rollback_on_error` and `verify_rollback`. Rollback
is capability-gated, permits only explicitly rollback-safe operations, and is
limited to graph node/link changes. It does not undo UMG, material, pin-value,
or other domain mutations.

## Validation

Validate Markdown links and confirm the three documents contain the new command
names, fingerprint requirement, and rollback limits. No runtime behavior or
tool signature changes are part of this documentation-only sync.
