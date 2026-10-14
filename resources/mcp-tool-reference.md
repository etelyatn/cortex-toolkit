# MCP Tool Reference

Flat catalog of all UnrealCortex MCP tools organized by domain.

## Tool Architecture

Tools fall into three categories:
- **Routers (12):** `core_cmd`, `data_cmd`, `blueprint_cmd`, `graph_cmd`, `level_cmd`, `material_cmd`, `umg_cmd`, `qa_cmd`, `reflect_cmd`, `editor_cmd`, `statetree_cmd`, `anim_cmd` — dispatch named commands to existing assets
- **Composites (7):** `blueprint_compose`, `material_compose`, `material_instance_compose`, `widget_compose`, `level_compose`, `scenario_compose`, `statetree_compose` — declarative creation workflows; `blueprint_compose(mode="update")` is a facade over one guarded `graph.apply_patch` envelope
- **Standalone (3):** `editor_restart`, `schema_generate`, `qa_test_step`

Rule: New asset creation → composite. Isolated edits to existing assets → router. Existing-asset graph edits → the guarded `graph.apply_patch` workflow (`resources/typed-blueprint-authoring.md`): context → describe → preview → apply → readback, persistence only on explicit authority. Whole function/macro/extra-event-graph or custom-event removal → `blueprint_cmd(command="remove_graph")` preview → apply instead, never a patch or compose workflow. The removed legacy update batch is never a fallback.

## Naming Convention

Most domain commands are accessed through **router tools** (`{domain}_cmd`). A few domains also have standalone MCP tools with typed parameters.

| Access Path | Pattern | Example |
|-------------|---------|---------|
| **Router tool** | `{domain}_cmd(command="name", params={...})` | `blueprint_cmd(command="get_info", params={"asset_path": "/Game/BP"})` |
| **Composite tool** | `{domain}_compose(spec)` | `blueprint_compose(...)` for new asset creation |
| **Standalone tool** (Reflect, some Editor/QA) | Direct function call | `query_class_hierarchy(class_name="AActor")` |

Router commands use **bare names** — e.g., `get_info`, `create`, `list` (NOT `get_blueprint_info`, `unknown_blueprint_command`).

**When in doubt:** Use the router tool `{domain}_cmd` with the bare command name from the lists below.

> Each router tool's docstring contains these same signatures. On parameter errors, re-read — never guess.

### Standalone tools vs the router passthrough

A standalone tool and the router route to the same native command but do **not** expose the same
parameters. The router passes parameters through verbatim, so any native parameter is reachable there
even when the standalone tool omits it. Known divergences:

| Command | Standalone tool exposes | Native-only (router only) |
|---------|------------------------|---------------------------|
| `blueprint.get_class_defaults` | `asset_path`, `properties`, `blueprint_path`, `include_values`, `include_members`, `discovery_offset`, `discovery_limit` | `changed_only` |
| `blueprint.set_class_defaults` | `asset_path`, `properties`, `compile`, `save`, `expected_fingerprint`, `items`, `blueprint_path` | `echo` |
| `editor.get_recent_logs` | `severity`, `since_seconds`, `since_cursor`, `category` | `until_cursor`, `limit`, `count_only` |
| `core.get_capabilities` | — | Python-only `detail` (`names` default / `full`) |

`get_capabilities` also differs the other way: the Python router adds a **Python-only** `detail`
parameter (`names|full`, default `names`) that is validated and stripped before the native call — the
native command receives no `detail`, and the default MCP view drops every command's `params` signature
inventory. Use `detail=full` (or `get_operation_schema` / `profile_operation_schema`) when you need the
per-command parameter signatures. Native `get_capabilities` itself declares no params and is not
self-listed in the `core` domain's command array.

---

## Response Handling

### Large Responses — Auto-Truncation

When a generic MCP response exceeds 40,000 characters, the response formatter finds the largest list with 10+ items, binary-searches for the max item count that fits, and returns `_truncated` metadata:

```json
{
  "rows": [...],
  "_truncated": {
    "original_count": 500,
    "returned_count": 42,
    "suggestion": "Pass 'limit' parameter to paginate through results."
  }
}
```

If no truncatable list exists, the response is replaced with `{"_error": "RESPONSE_TOO_LARGE"}`.

This budget bounds generic response delivery. `graph.apply_patch` prune uses a dedicated
complete-or-refuse boundary at `mcp_limits.max_response_chars=40000`: an incomplete or oversized
preview is refused rather than truncated, and an oversized apply is refused before mutation. Only
lossless large-island inventory retrieval remains unsupported future scope; the bounded response
guard is tracked at [CortexSandbox #102](https://github.com/etelyatn/CortexSandbox/issues/102).
See [`resources/typed-blueprint-authoring.md`](resources/typed-blueprint-authoring.md). **Stop and reconcile**
after any ambiguous or lost outcome; never approve a partial inventory, retry blindly, or treat a
response read as a pre-mutation gate.

### Complete-or-refuse reads

Reads that own an explicit selector never silently shorten a payload. When the condensed JSON would
exceed the 40,000-character ceiling they return a refusal envelope instead of a partial page, and the
generic `_truncated` marker is never used for them:

```json
{
  "_error": "RESPONSE_TOO_LARGE",
  "_message": "data.get_data_asset response exceeds 40000 characters; the complete read was refused.",
  "reader_complete": false,
  "_suggestion": "Select the needed members with 'fields' instead of reading the whole DataAsset."
}
```

`reader_complete=false` is the authoritative signal — never treat the absence of `_truncated` as proof
that a read was complete. Refusing reads narrow the request instead of retrying unchanged:
`data.get_data_asset` (`fields`), `material.get_node` (`properties`), `umg.get_tree`
(`depth`/`max_nodes`/`names_only`), `graph.get_subgraph` (`node_ids`/`include_edges`),
`blueprint.get_class_defaults` / `list_settable_defaults` / `list_inherited_properties`
(`properties`/`include_values`/`discovery_limit`), `data.get_data_catalog` (`sections`,
`include_asset_paths=false`), `get_capabilities` (`detail=names`), and
`reflect.class_detail`/`query_class_context` (`detail=summary`).

### Pagination

Pagination is **owned by the command**, not the transport. Two mechanisms exist and are not
interchangeable:

**Python cursor pages** — for list commands the Python layer caches, pass a Python-only `limit`
(integer 1–200) for a first page with `_pagination` metadata, then pass `cursor` (opaque token from
`_pagination.next_cursor`) to fetch the next page without re-calling C++:

```json
{
  "rows": [...],
  "_pagination": {
    "returned": 20,
    "total": 347,
    "has_more": true,
    "next_cursor": "eyJrZXkiOiAiYWJjMTIzIn0="
  }
}
```

Cache TTL is 60 seconds. On expiry, re-send the original command with `limit` to restart.

**Native-owned windows** — `data.query_datatable`, `data.search_datatable_content`,
`data.search_assets`, `level.list_actors`, `reflect.find_overrides`, `reflect.find_usages`,
`reflect.get_dependencies`, `reflect.get_referencers`, `reflect.search`, `statetree.list_assets`,
`editor.list_cvars`, `editor.get_recent_logs`, `anim.list_assets`, `gen.list_jobs`. Their
`limit`/`offset` (or the command's own cursor fields) are forwarded to the owner unchanged and the
native window is authoritative: no Python `cursor` is accepted (it is refused with `INVALID_CURSOR`),
the native `limit=0` "unlimited" sentinel keeps its owner meaning, and an oversized page refuses
rather than being shortened. Read the command's own completeness field — `is_complete`, `has_more`,
`truncated`, `tree_complete`, `next_offset`, `next_cursor` — instead of assuming a fixed page size or
a uniform `_pagination` envelope.

### Projection, filtering, and paging are different parameters

Do not conflate them:

- **Projection** (`fields`) is a whitelist of response keys or property paths. It never changes
  *which* objects are returned; omitting a key means "not requested", not "not present".
- **Filtering** (`class_names`, `path_prefixes`, `query`, `class_name`) selects the population.
- **Paging** (`offset`/`limit`, `since_cursor`/`until_cursor`, `discovery_offset`/`discovery_limit`)
  selects a slice of an already-filtered, already-ordered population. If your filter has no effect,
  check the parameter *name* against the command's schema before assuming the data is absent.

### Error Codes

| Code | Meaning | Recovery |
|------|---------|----------|
| `RESPONSE_TOO_LARGE` | Nothing truncatable, or a complete-or-refuse read refused an oversized page | Narrow the request: selectors/`fields`/`detail`/`sections`/`depth`/`limit` (see the refusal's `_suggestion`) |
| `INVALID_LIMIT` | Python `limit` not an integer in [1, 200] | Pass an integer in range, or use the command's native window |
| `INVALID_CURSOR` | Cursor token malformed, **or** a Python `cursor` was sent to a native-owned window | Restart Python pagination with `limit`; for a native window use its own `offset`/`since_cursor` |
| `CURSOR_EXPIRED` | Cached results expired (60s TTL) | Re-send original command with `limit` |

---

## Core (`core_cmd`)

- `get_status` — connection health, registered domains, engine/plugin versions
- `get_data_catalog` — unified project data overview (cached 10 min)
- `refresh_cache` — clear all cached MCP responses
- `schema_status` — check if `.cortex/schema/` exists, per-domain freshness and version (no editor required)
- `get_operation_schema` — live editor construction contract for one command (`domain`, `command`); returns `source`, `editor_instance_id`, `plugin_build_id`, `router`, `domain`, `command`, and `params`. A capabilities cache never proves a command is executable.
- `batch` — execute multiple commands sequentially with `$ref` resolution; see `resources/batch-pipeline-guide.md`
- `batch_query` — run multiple commands in one round-trip; requires exactly one non-empty `commands` or `steps` array and accepts `stop_on_error`, `rollback_on_error`, and `verify_rollback`. The latter two publish graph-rollback metadata only; actual rollback behavior depends on the editor implementation.
- `switch_editor` — select target editor by PID or index when multiple editors are running
- `shutdown` — graceful editor shutdown

`batch_query` accepts `rollback_on_error` and `verify_rollback`. Rollback is capability-gated and applies only to supported graph node/link operations; it does not undo pin-value, UMG, material, or other domain mutations.

### Profile-aware live schema contract

- `profile_operation_schema(profile, domain, command)` — returns a live-editor-backed contract with policy gating (`policy_allowed`), execution shape (`router`/`batch`), retry budget (`budget_remaining`), and restart guidance. Structured editor failures remain nested as `unreal_error: {code, message, details}`, including after retry-budget exhaustion. The default `UMGAuthoring` profile permits `umg`, `graph`, and `core` domains only. That gating is schema discovery, not call interception: a direct router call is not blocked by the profile, so the effective restriction is whatever filtering the external host applies — report a `policy_allowed: false` response as a stop signal, not as proof that a direct call would fail.

### Strict router envelope

All `{domain}_cmd` tools enforce the canonical shape `{command: string, params: object}`. Extra top-level operation fields or non-object `params` are rejected with `INVALID_INVOCATION_SHAPE`. `core.batch_query` rejects empty/missing/non-array `commands` locally before contacting the editor.

### Error preservation

Unreal errors are returned as `{"success": false, "_error": code, "_message": message, "_command": command, ...details}` without flattening nested `details`. Do not override reserved fields `success`, `_error`, `_message`, or `_command`.

### Asset Editor Commands (`core.*`)

Manage asset lifecycle. All commands accept a single path, a list of paths, or glob patterns (e.g., `/Game/Data/DT_*`).

- `save_asset` — persist in-memory changes to disk (`asset_path`, `force`, `dry_run`)
- `open_asset` — open asset editor tab(s) (`asset_path`, `dry_run`)
- `close_asset` — close asset editor tab(s) (`asset_path`, `save`, `dry_run`)
- `reload_asset` — discard in-memory changes and reload from disk; closes open tabs before reloading (`asset_path`, `dry_run`)

### Standalone

- `schema_generate` — generate LLM-readable `.cortex/schema/` files from live editor data (requires running editor) *(top-level MCP tool, not routed through core_cmd)*

---

## Data (`data_cmd`)

- **DataTables:** `list_datatables`, `get_datatable_schema`, `query_datatable`, `get_datatable_row`, `add_datatable_row`, `update_datatable_row`, `delete_datatable_row`, `search_datatable_content`, `import_datatable_json`, `get_struct_schema`
- **Raw/schema file exports:** `export_datatable_json`, `export_string_table_json`, `export_data_assets_json`, `export_schema_json`, `export_bulk_json`
- **Snapshot diff:** `compare_data_json`
- **File-backed imports:** `apply_import_ops_json`
- **GameplayTags:** `list_gameplay_tags`, `validate_gameplay_tag`, `register_gameplay_tag`, `register_gameplay_tags`, `resolve_tags`
- **DataAssets:** `list_data_assets`, `get_data_asset`, `update_data_asset`
- **CurveTables:** `list_curve_tables`, `get_curve_table`, `update_curve_table_row`
- **StringTables:** `list_string_tables`, `get_translations`, `set_translation`, `update_string_table`
- **Search:** `search_assets`

For large or repeatable data migrations, use raw export commands for large reads, `export_schema_json` for offline validation inputs, `compare_data_json` for exported-snapshot review, and `apply_import_ops_json` for the guarded write phase. Small targeted edits should still use direct mutation commands.

File-backed Data command responses use a compact summary envelope: `success`, `partial`, `warnings`, `errors`, `files_written`, `targets_touched`, and nested `counts`. Raw export payload files and durable import reports on disk remain the detailed sources of truth. For `apply_import_ops_json`, queue counts are exposed under normalized nested keys such as `operations`, `validated`, `previewed`, `attempted`, `applied`, `failed`, and `save_failed` instead of legacy summary aliases.

Use `export_schema_json` when the job is offline schema validation rather than raw payload review. It writes DataTable row schemas, transitive struct closure, DataAsset class property schemas, and StringTable metadata to disk while keeping the MCP response compact.

`get_data_asset` returns a deep reflected property payload. Inspect additive `partial` and `issues` fields before assuming every nested field serialized cleanly.

`export_data_assets_json(include_properties=true)` performs deep property export. In partial mode it can report `partial`, `issue_count`, and `omitted_assets`; in strict mode (`allow_partial=false`) blocking serialization issues fail the export instead of writing an incomplete asset set.

### Data Localization Migration Examples

Generic router dry-run prefix migration:

```json
{
  "tool": "data_cmd",
  "command": "update_string_table",
  "params": {
    "string_table_path": "/Game/Data/ST_CodexEntries.ST_CodexEntries",
    "dry_run": true,
    "verbose": false,
    "operations": [
      {"type": "replace_all", "old_prefix": "entry.", "new_prefix": ""}
    ]
  }
}
```

Dry-run `operation_results` are preview-only: successful operations report `applied=false`, `would_apply=true`, and `status="would_apply"`. Apply with `dry_run=false` only after the preview is clean or after intentionally setting `allow_partial=true`.

Optional direct compatibility wrapper, only if still registered:

```text
update_string_table(
  string_table_path="/Game/Data/ST_CodexEntries.ST_CodexEntries",
  operations_json="[{\"type\":\"replace_all\",\"old_prefix\":\"entry.\",\"new_prefix\":\"\"}]",
  dry_run=true,
  verbose=false
)
```

Scan DataTable `FText` references:

```json
{
  "tool": "data_cmd",
  "command": "search_datatable_content",
  "params": {
    "table_path": "/Game/Data/DT_CodexEntries.DT_CodexEntries",
    "search_mode": "string_table_refs",
    "string_table_path": "/Game/Data/ST_CodexEntries.ST_CodexEntries",
    "key_pattern": "entry.*",
    "limit": 100
  }
}
```

For `search_mode="string_table_refs"`, the generic `data_cmd` router forwards `limit` to C++ so scans can return more than the normal default batch size. Use `limit` as the scan cap; cursor pagination is not used for this mode.

Update nested `TArray<UStruct>` table-backed `FText` fields:

```json
{
  "tool": "data_cmd",
  "command": "update_datatable_row",
  "params": {
    "table_path": "/Game/Data/DT_CodexEntries.DT_CodexEntries",
    "row_name": "fireball",
    "row_data": {
      "Steps": [
        {
          "Description": {
            "value": "Charge flame.",
            "string_table": {
              "table_id": "/Game/Data/ST_CodexEntries.ST_CodexEntries",
              "key": "fireball.step_0"
            }
          }
        }
      ]
    },
    "dry_run": true
  }
}
```

### Snapshot Diff Example

Compare two exported snapshots and write the canonical diff report to disk:

```json
{
  "tool": "data_cmd",
  "command": "compare_data_json",
  "params": {
    "left_path": "Saved/CortexExports/baseline/quests.json",
    "right_path": "Saved/CortexExports/proposed/quests.json",
    "report_path": "Saved/CortexExports/diff/quests_diff.json",
    "mode": "datatable_rows",
    "ignore_fields": ["LastModified"],
    "include_equal": false
  }
}
```

Use `mode="auto"` only for canonical Cortex export wrappers. Use explicit modes for top-level arrays or custom wrappers, and inspect the report file on disk for the full added/removed/changed summary.

### File-Backed Import Queue Example

Preview a migration queue:

```json
{
  "tool": "data_cmd",
  "command": "apply_import_ops_json",
  "params": {
    "ops_path": "Saved/CortexImports/quest_cortex_ops.json",
    "report_path": "Saved/CortexImports/quest_import_report.json",
    "dry_run": true,
    "apply": false,
    "query_back": true,
    "stop_on_error": true,
    "allow_partial": false
  }
}
```

Real apply requires `dry_run=false` and `apply=true`. The MCP response is intentionally compact; inspect the JSON report on disk for per-operation results, warnings, failures, and query-back payloads.

### Read contracts

`search_assets` — `query` is a case-insensitive substring over asset name *or* object path;
`class_names` is an **exact** class-name filter (subclasses excluded); `path_prefixes` are canonical
mounted package folders (`/Game/X`, recursive on folder boundaries). Rows are projected over the
caller's `fields` whitelist (default `[path, name, class_name]`; allowed
`path|name|class_name|package_path`). It is **natively paged** by `offset`/`limit` (defaults `0`/`50`)
over a deterministic canonical object-path order applied *before* paging, so pages are stable:
`total_matches` is the exact filtered population independent of the page, and the next page is
`offset = next_offset` while `is_complete == false`. `count_only=true` returns before ordering with
`assets=[]`, `count=0`, exact `total_matches`, `is_complete=true`. Malformed arrays/prefixes/fields
refuse `INVALID_FIELD` before any registry fetch. The former scalar `class_filter`/`path_filter` reads
and the `total_before_limit` field are gone.

`list_data_assets` — the filter parameter is `class_name` (optional, subclass-aware via `IsChildOf`);
`path_filter` is unchanged. A caller still passing `class_filter` is silently not filtered, because the
field is no longer read at all.

`get_data_asset` — `fields` (optional array of non-empty paths) turns the read into a path-keyed
selected read; omitted/empty keeps the previous full deep reflected read. An unresolvable path refuses
`PropertyNotFound`. `partial`/`issues` are always present (`issues` may be empty); `warnings` appears
only when package capture produced warnings.

`get_data_catalog` — `sections` (allowed `datatables|gameplay_tags|data_assets|string_tables|curve_tables`;
omitted/empty builds every section; an unknown name refuses `INVALID_FIELD`). A section key absent from
the response means that section was not requested. `include_asset_paths` (default `false`) controls the
per-class `asset_paths` inventory inside `data_asset_classes[]`; the default response no longer carries
it. Reachable from both `data_cmd` and `core_cmd`.

---

## Blueprint (`blueprint_cmd`)

- **Assets:** `create`, `list`, `get_info`, `delete`, `duplicate`, `compile`, `save`, `rename`, `reparent`

`get_info` accepts an optional `compact` boolean parameter, **default `true`**. In compact mode, empty `inputs`/`outputs` arrays and the `source` field are omitted from the functions list — this mostly reduces noise from inherited functions. Pass `compact: false` when you need to distinguish `"blueprint"` vs `"inherited"` sources or verify full parameter signatures (e.g., during BP→C++ migration analysis).
- **Structure:** `add_variable`, `remove_variable`, `add_function`, `get_class_defaults`, `set_class_defaults`, `configure_timeline`, `set_component_defaults`, `add_scs_component`, `remove_scs_component`, `rename_scs_component`
- **Class Settings:** `add_interface`, `remove_interface`, `set_tick_settings`, `set_replication_settings`
- **Migration:** `analyze_for_migration`, `cleanup_migration`, `remove_scs_component`, `rename_scs_component`, `recompile_dependents`, `fixup_redirectors`, `compare_blueprints`
- **Graph maintenance:** `delete_orphaned_nodes`, `remove_graph`, `search`

`remove_graph` deletes a whole function, macro, extra event graph, or custom event through `blueprint_cmd(command="remove_graph")`; it is not `graph.apply_patch` or `blueprint_compose`. It requires strict boolean `dry_run`, `compile`, and `save`; optional strict `cascade_exec_chain` defaults to `false`. Preview (`dry_run=true`, `save=false`) returns `fingerprint_before` and `validation_hash`; apply requires both as `expected_fingerprint` and `expected_validation_hash`. `compile=false` never saves, and `save=true` requires `compile=true` and a clean starting package; EventGraph and ConstructionScript are protected. Full semantics: [CortexBlueprint system reference](https://github.com/etelyatn/CortexSandbox/blob/main/docs/systems/cortex-blueprint.md#guarded-graph-removal).
- **Level Blueprint:** Use `get_level_blueprint(map_path)` (standalone tool) to get a synthetic path, then use `graph_cmd` commands. Save with `level_cmd(command="save_level")`, not `blueprint_cmd(command="save")`.

### Class default reads and writes

`get_class_defaults`, `list_settable_defaults` and `list_inherited_properties` share one read contract.
`properties` is a **selector**: non-empty ⇒ an effective-value read of those paths (unpaged, `value`
present by default). Empty/absent ⇒ **metadata discovery** over the whole admitted population, paged by
`discovery_offset`/`discovery_limit` (defaults `0`/`100`, limit 1–200) and **without values** unless
`include_values=true`. Omission is a verdict, not a missing field: no `value` ⇒ not requested (or
`include_members`/`changed_only` semantics below); no `discovery_pagination` ⇒ the read was not a paged
metadata read; no `total_properties` ⇒ the read had a `properties` selector. Follow
`discovery_pagination.next_offset` while `is_complete == false`.

`include_members=true` expands one level of struct-member metadata (member *values* only with
`include_values=true`). `changed_only=true` (only on `get_class_defaults`) switches to an
**inherited-delta read**: it requires `include_values=true` (explicit `false` refuses), excludes
`include_members` (refuses), and reports `value_mode="inherited_delta"`, `baseline_class`,
`effective_values_complete=false`, `echo_complete`, and `omitted_equal_properties` — a root listed there
provably equals its baseline; an incomplete comparison is flagged, never reported as equal.
`list_settable_defaults`/`list_inherited_properties` refuse `changed_only`. Bad `properties`/control types
refuse `INVALID_FIELD` before any asset load.

`set_class_defaults` gained a per-property `echo` selector (string, default `"diff"`; one of
`diff|full|none`, anything else refuses `INVALID_FIELD`); it affects only the echo, never what is applied,
compiled or saved. Every property record carries `changed` in every mode. `echo=full` returns the
`previous_value`/`new_value` pair; `echo=diff` (default) omits the echo entirely when unchanged, returns
a `changes` map of relative leaf paths for a struct root (plus `value_encodings` for a wide int64 leaf),
and the `previous_value`/`new_value` pair for a scalar/collection root; `echo=none` returns only
`changed`. `FSoftObjectPath`, `FGameplayTag`, `FGameplayTagContainer` and `FInstancedStruct` roots are
always echoed atomically, never as leaf paths.

### Composite

- `blueprint_compose` — atomic creation of a new Blueprint with variables, functions, and initial graph nodes
- `blueprint_compose(mode="update", asset_path=..., patch={...})` — forwards exactly one reviewed
  `graph.apply_patch` envelope (the facade owns `asset_path` and refuses a conflicting
  `patch.asset_path`); a legacy `nodes`/`connections` update arrives without a `patch` and is refused
  with `MIGRATION_REQUIRED`

---

## Graph (`graph_cmd`)

- `list_graphs`, `list_nodes`, `get_node`, `search_nodes`, `describe_node`, `add_node`, `remove_node`, `connect`, `disconnect`, `set_pin_value`, `auto_layout`, `get_authoring_context`, `apply_patch`
- `set_pin_value`: use `value` for non-text pins and literal-only simple values; use structured `text` for `FText` pins, especially StringTable-backed text. `value` and `text` are mutually exclusive.

Use `describe_node` before raw `add_node` authoring to inspect the accepted class, parameters, and pins. Correct an invalid request before attempting the mutation. Invoke it as `graph.describe_node` through `graph_cmd`.

`get_authoring_context` publishes candidate graphs, canonical GUIDs, mutability, subgraph paths,
fingerprint and native limits; `apply_patch` previews and applies one guarded graph patch. Read the
live schema before building requests. The bounded complete-or-refuse MCP prune route is implemented;
oversized apply is refused before mutation. Only lossless large-island inventory retrieval remains
unsupported future scope; the bounded response guard is tracked at
[CortexSandbox #102](https://github.com/etelyatn/CortexSandbox/issues/102).
See [`resources/typed-blueprint-authoring.md`](resources/typed-blueprint-authoring.md) for the exact
preflight and refusal fields. Every `core_cmd(batch_query)` rejects nested `graph.apply_patch` before
any subcommand, regardless of rollback settings; mutation approval is not paginated.

`list_graphs` returns user-visible Blueprint graphs. Top-level entries include `kind`
(`ubergraph`, `function`, `macro`, `delegate`, or `interface_impl`); `interface_impl`
entries also include `owning_interface`. Delegate graphs are readable but not mutable
through generic graph commands.

Generic read commands resolve graphs by name: if names collide across categories they resolve the
first match, so prefer unique names. Authoring does not rely on that resolution — a patch target is a
`graph_ref` carrying a canonical `graph_guid` (plus an optional `subgraph_path`) taken from
`graph.get_authoring_context`.

`auto_layout` — repositions node bodies using execution-first left-to-right layout with parameter grouping. `mode`: `"full"` repositions eligible non-comment nodes; `"incremental"` only repositions nodes at `(0,0)` while reserving established bodies without moving them. Optional `graph_name`, `horizontal_spacing`, `vertical_spacing`. To target a composite child, supply both the root `graph_name` and its dot-separated `subgraph_path`; a child path without a root is refused.

The response reports eligible `node_count`, `graphs_processed`, actual `changed_node_count`, and `unchanged`. A repeated unchanged layout does not dirty the asset. Layout never saves implicitly: use explicit asset persistence after inspection. Read graph/node data with `compact: false` to verify positions, and inspect the actual Blueprint Editor surface; a success response alone is not visual or save/reload proof.

### Compact Serialization (default for read commands)

`list_nodes`, `get_node`, and `search_nodes` accept an optional `compact` boolean parameter, **default `true`**. Compact mode strips fields AI agents rarely need, reducing response size by ~25-35% on typical graphs.

| Command | `compact=true` strips |
|---------|----------------------|
| `list_nodes` | `position` object, `node_class` (duplicate of `class`), `pin_count` |
| `get_node` | `position`, `node_class`, hidden pins with no connections/defaults, `is_connected: false`, empty `default_value` |
| `search_nodes` | `node_class` (duplicate of `class`) — no positions in search results to begin with |

**Pin skip predicate** (`get_node` only): a pin is excluded only when ALL of `bHidden`, no `LinkedTo`, empty `DefaultValue`, empty `DefaultTextValue`, AND `DefaultObject == nullptr`. Hidden class-reference pins with meaningful defaults are preserved.

**Pass `compact: false` when:**
- Debugging visual layout (need `position` x/y)
- Inspecting every hidden pin (e.g., tunnel boundaries, world-context pins)
- Generating C++ from a BP graph (migration correctness — Ground Truth Table needs full fidelity)
- Running asserts against field presence in tests

See `blueprint-patterns.md` for node class short names and full node type table.

---

## Material (`material_cmd`)

- **Asset:** `list_materials`, `get_material`, `create_material`, `delete_material`, `set_material_property`
- **Instances:** `list_instances`, `get_instance`, `create_instance`, `delete_instance`
- **Parameters:** `list_parameters`, `get_parameter`, `set_parameter`, `set_parameters`, `reset_parameter`
- **Graph:** `list_nodes`, `get_node`, `add_node`, `remove_node`, `list_connections`, `connect`, `disconnect`, `auto_layout`, `set_node_property`, `get_node_pins`
- **Collections:** `list_collections`, `get_collection`, `create_collection`, `delete_collection`, `add_collection_parameter`, `remove_collection_parameter`, `set_collection_parameter`
- **Dynamic Instances (PIE):** `list_dynamic_instances`, `get_dynamic_instance`, `create_dynamic_instance`, `destroy_dynamic_instance`, `set_dynamic_parameter`, `get_dynamic_parameter`, `list_dynamic_parameters`, `set_dynamic_parameters`, `reset_dynamic_parameter`

`get_node` accepts an optional `properties` selector (array of non-empty property names). Omitted/empty
keeps the previous full editable read. A selected read keys `properties` by the requested selector and
validates the root segment against the same editable admission as the full read (a dotted path cannot
cross a non-editable root); an unknown or non-editable name refuses `PropertyNotFound`.

### Composites

- `material_compose` — atomic creation of a new Material with nodes and connections
- `material_instance_compose` — atomic creation of a new Material Instance with parameter overrides

---

## UMG (`umg_cmd`)

- **Tree:** `add_widget`, `remove_widget`, `reparent`, `get_tree`, `get_widget`, `list_widget_classes`, `duplicate_widget`, `set_widget_variable`
- **Properties:** `set_color`, `set_text`, `set_font`, `set_brush`, `set_padding`, `set_anchor`, `set_alignment`, `set_size`, `set_visibility`, `set_property`, `get_property`, `get_schema`
- **Animations:** `create_animation`, `list_animations`, `remove_animation`, `list_animation_bindings`, `ensure_animation_binding`, `set_animation_property_track`, `remove_animation_binding`

`get_widget` returns `render_transform`, `slot_type` (e.g. `"CanvasPanelSlot"`, `null` for root), and `slot` (layout details vary by slot type).

`get_tree` is a bounded read. `depth` (root is level 0; present values must be strict integers `>= 0`)
and `max_nodes` (widgets emitted, root included; strict integer `>= 1`) cap the traversal; both are
absent ⇒ unlimited. `names_only=true` keeps hierarchy/name/child counts and drops class identity.
The response reports exact asset-wide `total_widgets` (never reduced by the budget),
`returned_widgets`, `tree_complete` (`!(depth cut || node cut)`) and a `reasons` array — one entry per
cut reason. `tree_complete` and `returned_widgets` are the authoritative completeness signals; a branch
stopped by either budget keeps its real `child_count` and is marked `incomplete: true` rather than
pretending to be a leaf, and a true leaf omits `child_count`/`children` entirely (leaf nodes no longer
carry `children: []`). With `include_property_bindings=true` the combined payload is measured as the
condensed model-facing JSON: over the module ceiling the command returns a refusal envelope
(`_error="RESPONSE_TOO_LARGE"`, `reader_complete=false`, `asset_path`, `total_widgets`,
`returned_widgets`, `max_response_chars`) with no `root`. There is no pagination — re-request with a
smaller `depth`/`max_nodes` or `names_only=true`.

`list_animation_bindings` returns canonical `FWidgetAnimationBinding` records, possessables, tracks, channels, and a version-2 content-guard `fingerprint`. Add `include_track_content: true` to include each supported float/color track's `property_path`, `type`, canonical evaluation state and sections/channels with per-channel `{frame_number, time_seconds, value, interpolation}`. A detailed page that exceeds the response ceiling returns `_error: "RESPONSE_TOO_LARGE"` with `reader_complete: false` and summary counts instead of a partial page; `pagination.is_complete` independently reports whether every binding was returned. `remove_animation_binding` surgically removes a single binding record by selector (`{widget_name, slot_widget_name, binding_guid, is_root_widget}`) using optimistic locking (`expected_fingerprint`), defaulting to `dry_run=true` and `save=false`. Shared MovieScene possessables and tracks are preserved. Renaming a Designer widget propagates its binding `WidgetName` and possessable name; a stale `expected_fingerprint` refuses with `STALE_PRECONDITION` and the current fingerprint, without mutation.

**Guarded animation authoring:** `ensure_animation_binding` creates or resolves the ordinary Designer-widget binding for `widget_name` (the flag stays `is_root_widget: false`; root-user-widget, slot and dynamic bindings are refused). `set_animation_property_track` creates, replaces or clears exactly one `float`/linear-color property track on an existing binding, addressed by `selector`, `property_path` and a `track` object (`type` plus half-open `sections` with `time_seconds`/`value`/`interpolation` keys); `track: null` clears one property track while retaining the binding. Both commands require the full content-guard `fingerprint` from `list_animation_bindings` as `expected_fingerprint`, reject any supplied cursor/limit/offset field, default `dry_run` to `true`, and never compile or save. Limits: ordinary Designer widgets, at most 8 sections and 64 logical keys per track, and a 32,000-character prospective response budget. See `resources/umg-patterns.md` for the full workflow.

`set_widget_variable` changes the designer-variable flag on an existing Widget Blueprint. Inspect the current widget tree first and pass its current `expected_fingerprint`. Invoke it as `umg.set_widget_variable` through `umg_cmd`.

**Designer property bindings:** opt in with `include_property_bindings=true` on
`get_widget` (widget scope) or `get_tree` (asset scope, including orphan targets).
`property_binding_state` includes complete serialized source identities, reader
completeness and an asset-level fingerprint. `set_property_binding` requires asset,
widget, target `property_name`, explicit `binding` and `expected_fingerprint`.
An object creates/replaces a compatible property path or pure function; explicit null
clears. Omitted/empty values refuse; duplicate targets and stale guards are non-destructive.
No implicit compile/save/reload and no pagination fields. This uses existing `umg_cmd`,
not a new MCP tool, and does not change literal `set_property` or animation bindings.

### Composite

- `widget_compose` — atomic creation of a new UMG Widget Blueprint with an initial widget hierarchy

---

## Animation (`anim_cmd`)

- **Inspection:** `list_assets`, `get_sequence_info`, `get_montage_info`, `get_skeleton_info`, `get_animbp_info`
- **Guarded authoring:** named notifies, float curves, montage sections, skeleton sockets, object notifies, and notify states.
- Object notify selectors use `{ index, class_path, time }`; notify-state selectors also include `duration`.
- Every mutation requires `expected_fingerprint`, supports `dry_run`, and defaults `save` to `false`. Only live capabilities advertise authoring families; later-stage animation systems remain unavailable.

---

## Level (`level_cmd`)

- **Actors:** `spawn_actor`, `delete_actor`, `duplicate_actor`, `rename_actor`, `get_actor`, `set_transform`, `set_actor_property`, `get_actor_property`, `list_actors`, `find_actors`, `get_bounds`, `select_actors`, `get_selection`
- **Components:** `list_components`, `add_component`, `remove_component`, `get_component_property`, `set_component_property`
- **Discovery:** `list_actor_classes`, `list_component_classes`, `describe_class`
- **Organization:** `attach_actor`, `detach_actor`, `set_tags`, `set_folder`, `group_actors`, `ungroup_actors`
- **Level management:** `get_info`, `list_sublevels`, `load_sublevel`, `unload_sublevel`, `set_sublevel_visibility`, `list_data_layers`, `set_data_layer`, `save_level`, `save_all`

`list_components` gained `include_properties` (boolean, default `false`). Only with `true` does each
component carry `properties` (at most the first 20 admitted `CPF_Edit|CPF_BlueprintVisible` values),
`total_property_count`, `returned_property_count` (≤ 20) and `properties_complete` (`total == returned`).
The four property keys are absent because they were not requested — never because a component has no
properties, which `properties_complete` distinguishes from a truncated page.

### Composite

- `level_compose` — atomic placement of multiple actors with transforms in a single batch

---

## StateTree (`statetree_cmd`)

- **Assets:** `list_assets`, `create_asset`, `duplicate_asset`, `delete_asset`
- **Inspection:** `dump_tree`, `get_state`, `check_structure`
- **Validation/Compile:** `validate_asset`, `compile`
- **States:** `add_state`, `remove_state`, `rename_state`, `move_state`, `set_state_properties`
- **Transitions:** `add_transition`, `remove_transition`, `set_transition_properties`

Mutating commands require `expected_fingerprint` for existing assets. Use `dump_tree` or `check_structure` to get the current fingerprint before mutation. `validate_asset` and `compile` can dirty assets, so do not call them during read-only review.

### Composite

- `statetree_compose` — create or update one StateTree from declarative states and transitions, with fingerprint threading, update-mode preflight, optional validation, optional compile, optional save, and create-mode cleanup on failure.

Current boundary: StateTree support is structure-level. It does not author arbitrary tasks, conditions, evaluators, parameter bags, or property bindings.

---

## Animation (`anim_cmd`)

- **Assets:** `list_assets`
- **Inspection:** `get_sequence_info`, `get_montage_info`, `get_skeleton_info`, `get_animbp_info`
- **Named notifies:** `add_named_notify`, `update_named_notify`, `remove_named_notify`
- **Float curves:** `add_curve`, `set_curve_keys`, `remove_curve`
- **Montage sections:** `add_montage_section`, `update_montage_section`, `remove_montage_section`
- **Skeleton sockets:** `add_socket`, `set_socket_transform`, `remove_socket`
- **Object notifies:** `add_notify`, `update_notify`, `remove_notify`
- **Notify states:** `add_notify_state`, `update_notify_state`, `remove_notify_state`

Every mutating command requires the shared Cortex `expected_fingerprint`, supports
`dry_run`, and defaults `save` to `false`. Inspect the matching asset first, then pass its
`fingerprint` as `expected_fingerprint`. Use an authoring family only when live capabilities
advertise that complete family.

Current boundary: Animation authoring covers sequence skeleton named/object notifies, notify
states, editable float curves, montage sections, and skeleton sockets. AnimBP authoring,
blendspaces, retargeting, runtime preview, Sequencer, and Control Rig are out of scope. There is no
`anim.save_asset`; use a mutation's `save=true` option, or `core.save_asset` where appropriate.

---

## Editor (`editor_cmd`)

- **PIE lifecycle:** `start_pie`, `stop_pie`, `get_pie_state`, `pause_pie`, `resume_pie`, `restart_pie`
- **Viewport:** `get_viewport_info`, `capture_screenshot`, `set_viewport_camera`, `focus_actor`, `set_viewport_mode`
- **Utilities:** `get_editor_state`, `get_recent_logs`, `execute_console_command`, `set_time_dilation`, `get_world_info`
- **Input injection** (requires active PIE): `inject_key`, `inject_mouse`, `inject_input_action`, `inject_input_continuous`, `inject_input_sequence`

See `qa-patterns.md` for input injection documentation.

`get_recent_logs` is a finite, natively-paged log **window**, not a tail. Seven parameters:
`severity` (`log|warning|error`, minimum level, default `log`), `since_seconds` (default `30.0`;
**exactly `-1`** disables time filtering and any other negative refuses `INVALID_FIELD`),
`since_cursor` (default `-1` ⇒ from the beginning of the ring), `until_cursor` (**inclusive**
end-of-window watermark; rows past it are never attributed to this window), `limit`
(1–2000, default `200`), `count_only` (default `false`), `category` (exact match, default `""`).
The response reports `entries` (`{cursor, timestamp, category, message, severity}` — canonical
lowercase severity), `count`, `next_cursor`, `latest_cursor`, `window_end_cursor`,
`oldest_available_cursor`, `matched_count` (matches in the window regardless of page size),
`has_more`, and `lost_before_cursor` (rows before the requested start were evicted from the ring).
The window is `(since_cursor, window_end_cursor]`. Next page: `since_cursor = next_cursor` while
`has_more == true`, **pinning `until_cursor = window_end_cursor` from the first page** so a
late-arriving record is not attributed to this window. `count_only=true` returns `entries=[]`,
`next_cursor=window_end_cursor`, `has_more=false` with exact `matched_count` — the standard way to
capture a baseline watermark. `lost_before_cursor=false` means no loss was *proven*, not that history
is complete. The former string `since_cursor`, duplicate `logs` array and scalar `cursor` field are
gone.

The standalone `get_recent_logs` tool exposes only `severity`, `since_seconds`, `since_cursor` and
`category` and forwards only those; `until_cursor`, `limit` and `count_only` are reachable through the
`editor_cmd` router passthrough. Prefer the standalone tool for a quick tail and `editor_cmd` for a
pinned window.

`execute_console_command` requires active PIE. It first preserves world Exec dispatch,
then processes unhandled input through the console manager with the same PIE world.
Handled input is not dispatched again. Unknown input returns `CONSOLE_COMMAND_FAILED`;
inactive PIE returns `PIE_NOT_ACTIVE`. Success means dispatch was accepted, not that a
void callback completed without an application error. Verify the command's observable
effect or callback logs rather than relying only on `status: "ok"`.

Enhanced Input uses canonical `action_name`, not `action`: finite numeric `value` or
`{x,y,z}` shaped to the action type. Continuous start/update/stop is immediate unless
a positive start-only `duration_ms` requests deferred completion. Updates require
the same session-owned subsystem/action; stop does not stop game-managed injections.
Cleanup stops owned native entries on disconnect/PIE end; ownership is session-wide.
Confirm gameplay effects, not only registration.

`capture_screenshot` redraws the active viewport and returns `view`, `pie_active` and
`camera_available`. Only `camera_provenance=editor_client` has a `camera` pose; game-view
pose is unavailable, not guessed. No `source` selector. `set_viewport_camera` requires
`location={x,y,z}` and optionally `rotation={pitch,yaw,roll}`. Possessed PIE rejects by
default; Boolean `allow_during_pie=true` changes only the transient editor client,
not the rendered game camera. Read `editor_camera_visible`; engine restoration may
discard the override. Ejected/SIE editor views remain controllable.

### Standalone

- `editor_restart` — restart the Unreal Editor process

---

## QA (`qa_cmd`)

- **World queries:** `observe_state`, `get_actor_state`, `get_player_state`
- **Game actions:** `look_at`, `interact`, `move_to`, `wait_for`, `teleport_player`, `set_actor_property`, `set_random_seed`
- **Assertions:** `assert_state`
- **Recording/Replay:** `start_recording`, `stop_recording`, `replay_session`, `cancel_replay`

### Standalone

- `qa_test_step` — execute a single declarative QA test step (used by scenario runner)

`qa_test_step` and `run_scenario` (scenario_compose) emit a per-step/summary `log_coverage` object
(`{complete, lost_before_cursor, window_end_cursor, count, cause}`). It is built on a single one-shot
finite `editor.get_recent_logs` window (a `count_only` baseline watermark, then `since_cursor` with a
pinned `until_cursor`, `limit=200`, page cap 50) with no retry or poll. `complete=false` is forced by
front eviction, an MCP/native size refusal, a read failure, non-advancing pagination, a missing
watermark, or the page cap; `cause` names which. Treat `complete=false` as "log coverage unknown", not
as "no errors occurred". The older unconditional `max_lines`/`cursor` reads are gone, and log-severity
detection reads `recent_logs.entries[].severity` (lowercase) rather than the removed `logs[].level`
plus `"Error:"` text heuristic.

### Composite

- `scenario_compose` — atomic creation of a new QA scenario asset

---

## Reflect

Reflect is reachable **two ways**:
- **Standalone MCP tools** (recommended, typed parameters): `query_class_hierarchy`,
  `query_class_detail`, `query_class_context`, `query_overrides`, `query_usages`,
  `get_dependencies`, `get_referencers`, `impact_analysis`, `rebuild_graph_cache`,
  `reflect_cache_status`, `scan_project`
- **The `reflect_cmd` router** for the native commands (`reflect.class_detail`,
  `reflect.class_hierarchy`, `reflect.search`, `reflect.find_overrides`, `reflect.find_usages`,
  `reflect.get_dependencies`, `reflect.get_referencers`)

Standalone tools and native commands are not interchangeable:

`query_class_detail` defaults to `detail="summary"` and accepts `summary|properties|full`, refusing an
unknown value client-side; it maps `properties` to a native `full` read plus a Python allowlist and
always injects `detail`. The **native** `reflect.class_detail` default is `full` and it accepts **only**
`summary`/`full` — anything else refuses `INVALID_FIELD` (`Invalid detail '<x>'; expected 'summary' or
'full'`) instead of degrading to the expensive full read. `summary` omits `properties`, `functions` and
`components`. Callers that previously passed an ad-hoc value such as `"name"` and silently got `full`
must now pass `summary`.

`reflect.class_hierarchy` gained `include_flat_classes` (boolean, default `false`). The default response
no longer emits `classes` (pass `include_flat_classes=true` for the flat name list). It now reports
`total_classes`, `cpp_count`, `blueprint_count`, `project_cpp_count`, `engine_cpp_count`,
`project_blueprint_count`, and a new `truncated` boolean set by the walk itself. `truncated` is the
authoritative completeness signal: the `max_results` budget is shared by the whole recursive walk
(intermediaries and deeper nodes consume it), so the emitted child count cannot prove completeness, and
there is no pagination — re-request with a larger `max_results`/`depth`. `query_class_context` derives
`children_complete = !truncated`, bounds children at `max_results=20`, and fetches the parent through a
native `detail=summary` read.

`reflect.search` response changed: `results` is unchanged, plus new `returned` (page length),
`total_matches` (every match counted even past `limit`) and `truncated` (`total_matches > returned`).
The former `total_results` — which was only the returned page length — is removed with no alias.

---

## Convention

Resources use full router syntax: `domain_cmd(command="name", params={...})`. Agent `.md` files use bare command names (e.g., `list`) for readability.
