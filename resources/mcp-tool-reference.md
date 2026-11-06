# MCP Tool Reference

Flat catalog of all UnrealCortex MCP tools organized by domain.

## Tool Architecture

Tools fall into three categories:
- **Routers (13):** `core_cmd`, `data_cmd`, `blueprint_cmd`, `graph_cmd`, `level_cmd`, `material_cmd`, `umg_cmd`, `qa_cmd`, `reflect_cmd`, `editor_cmd`, `statetree_cmd`, `anim_cmd`, `replay_cmd` — dispatch named commands to existing assets. `anim_cmd` and `replay_cmd` are optional: they exist only when live capabilities prove the editor exposes those domains.
- **Composites (7):** `blueprint_compose`, `material_compose`, `material_instance_compose`, `widget_compose`, `level_compose`, `scenario_compose`, `statetree_compose` — declarative creation workflows; `blueprint_compose(mode="update")` is a facade over one guarded `graph.apply_patch` envelope
- **Standalone (3):** `editor_restart`, `schema_generate`, `qa_test_step`

Rule: New asset creation → composite. Isolated edits to existing assets → router. Existing-asset graph edits → the guarded `graph.apply_patch` workflow (`resources/typed-blueprint-authoring.md`): context → describe → preview → apply → readback, persistence only on explicit authority. Whole function/macro/extra-event-graph or custom-event removal → `blueprint_cmd(command="remove_graph")` preview → apply instead, never a patch or compose workflow. The removed legacy update batch is never a fallback.

## Naming Convention

Most domain commands are accessed through **router tools** (`{domain}_cmd`). A few domains also have standalone MCP tools with typed parameters.

| Access Path | Pattern | Example |
|-------------|---------|---------|
| **Router tool** | `{domain}_cmd(command="name", params={...})` | `blueprint_cmd(command="get_info", params={"asset_path": "/Game/BP"})` |
| **Composite tool** | `{domain}_compose(spec)` | `blueprint_compose(...)` for new asset creation |
| **Standalone tool** (Reflect, some Editor/QA) | Direct function call | `query_class_hierarchy(root="AActor")` |

Router commands use **bare names** — e.g., `get_info`, `create`, `list`. Never prefix them with the domain or the old wrapper style.

**When in doubt:** Use the router tool `{domain}_cmd` with the bare command name from the lists below.

> Router docstrings list command **names only**; parameter signatures are published through the
> capability inventory and `core.get_operation_schema`. On parameter errors, re-read — never guess.

### Standalone tools vs the router passthrough

A standalone tool and the router route to the same native command but do **not** expose the same
parameters. The router passes parameters through verbatim, so any native parameter is reachable there
even when the standalone tool omits it. Two exceptions are the Python-owned pagination controls:
`limit`/`cursor` are consumed by the commands that page in Python, and a `limit` outside 1–200 is
refused before dispatch with `INVALID_LIMIT` for any command — so an out-of-range `limit` returns that
rather than the native `INVALID_FIELD` a strict command gives an in-range undeclared `limit`. Eight
routed commands now enforce their
declared parameter set
— `umg.set_text`, `umg.set_font`, `umg.set_padding`, `umg.set_anchor`, `umg.set_alignment`,
`umg.set_size`, `data.list_data_assets`, `data.search_assets` — so for those an undeclared parameter is
refused with `INVALID_FIELD` naming the accepted set (as is a missing declared-required parameter)
instead of being silently dropped. Known divergences:

| Command | Standalone tool exposes | Native-only (router only) |
|---------|------------------------|---------------------------|
| `blueprint.get_class_defaults` | `asset_path`, `properties`, `blueprint_path`, `include_values`, `include_members`, `discovery_offset`, `discovery_limit` | `changed_only` |
| `blueprint.set_class_defaults` | `asset_path`, `properties`, `compile`, `save`, `expected_fingerprint`, `items`, `blueprint_path` | `echo` |
| `editor.get_recent_logs` | `severity`, `since_seconds`, `since_cursor`, `category` | `until_cursor`, `limit`, `count_only` |
| `get_capabilities` | — | Python-only `detail` (`names` default / `full`) |

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
`data.get_data_asset` (`fields`), `material.get_material` (`properties`/`include_input_state`),
`material.list_connections` (`include_input_state`), `material.get_node` (`properties`), `umg.get_tree`
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

The cache keeps 16 snapshots for 10 minutes. Every stored result gets a monotonically increasing `snapshot_id`, carried inside the cursor and reported in `_pagination`, so two identical requests keep independent cursors instead of replacing each other. On expiry, re-send the original command with `limit` to restart (never for `core_cmd` `batch_query`, see below).

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
| `INVALID_FIELD` | Parameter outside a command's declared set, or a declared-required parameter missing — on the enforcement-opted commands above; also a request that names no settable field | Pass only declared parameter names (the refusal lists the accepted set) and supply the declared-required ones |
| `INVALID_PROPERTY_VALUE` | Value is not a token the command accepts (for example an unknown anchor `preset`, alignment or `size_rule`) | Use one of the values named in the refusal |
| `INVALID_LIMIT` | Python `limit` not an integer in [1, 200] | Pass an integer in range, or use the command's native window |
| `INVALID_CURSOR` | Cursor token malformed, **or** a Python `cursor` was sent to a native-owned window | Restart Python pagination with `limit`; for a native window use its own `offset`/`since_cursor` |
| `CURSOR_EXPIRED` | Cached results expired (10-minute TTL, 16 snapshots) | Re-send original read with `limit`; for `batch_query` do NOT re-run the batch, its steps may mutate: the executed results were not recoverable, so verify state by readback |

---

## Core (`core_cmd`)

- `get_status` — connection health, registered domains, engine/plugin versions
- `get_data_catalog` — unified project data overview (cached 10 min)
- `refresh_cache` — clear all cached MCP responses
- `schema_status` — check if `.cortex/schema/` exists, per-domain freshness and version (no editor required)
- `get_operation_schema` — live editor construction contract for one command (`domain`, `command`); returns `source`, `editor_instance_id`, `plugin_build_id`, `router`, `domain`, `command`, and `params`. A capabilities cache never proves a command is executable.
- `batch_query` — the MCP-facing batch: run multiple commands in one round-trip with `$ref` resolution (see `resources/batch-pipeline-guide.md`); the router forwards it to the editor's native `batch` command, which `core_cmd` does not expose under that name. Requires exactly one non-empty `commands` or `steps` array and accepts `stop_on_error`, `rollback_on_error`, and `verify_rollback`. The latter two publish graph-rollback metadata only; actual rollback behavior depends on the editor implementation.
- `switch_editor` — select target editor by PID or index when multiple editors are running
- `shutdown` — graceful editor shutdown

`batch_query` accepts `rollback_on_error` and `verify_rollback`. Rollback is capability-gated and applies only to supported graph node/link operations; it does not undo pin-value, UMG, material, or other domain mutations.

`batch_query` also accepts the Python-owned `limit` and `cursor`. The batch executes exactly once; its `results` are stored as a snapshot and pages are served from that snapshot, never by re-executing. Without `limit`, a response that fits is returned whole. An oversized response never discards the executed results and never advises re-running: the first page that fits comes back with `_pagination` (`next_cursor`, `snapshot_id`) and a `_note` saying the batch already executed and the remaining step results are available by `cursor`.

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
- `list_redirectors` — read-only inventory of the redirectors under a content folder (`path`, `recursive` default `true`): `redirector_path`, `destination`, `referencer_count`, `referencers`; fixes up, deletes and saves nothing

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

`get_struct_schema` accepts a struct short name, the `F`-toggled name, or an object path under any mounted package root (`/Script/Module.FMyStruct`, a `/Game/...` user struct asset, plugin or engine content). An object path is loaded only when it exists and the Asset Registry says it is a struct; a non-struct asset is refused without loading.

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
`path_filter` is unchanged. The retired `class_filter` is refused with `INVALID_FIELD` naming the
accepted parameters, because `list_data_assets` enforces its declared parameter set rather than
silently ignoring an undeclared filter.

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

`list` takes `path`, `type` and `exclude_types`. `type` selects one family and `exclude_types` (array) removes families; they combine and are case-insensitive. Vocabulary, in classifier precedence: `Interface`, `FunctionLibrary`, `MacroLibrary`, `AnimBlueprint`, `EditorUtility`, `Widget`, `Component`, `Actor`, `Object` (any other resolved UObject parent), `Unknown` (parent unresolvable). An unknown value is refused with `INVALID_FIELD` listing the vocabulary. Rows carry `type`, `asset_class`, `parent_class` (the immediate parent; for a Blueprint parent, its asset name without `_C`), `parent_class_path`, and `native_parent_class`. The `blueprints` array pages through the Python `limit`/`cursor` mechanism below. `get_info` and `analyze_for_migration` report the same `type` vocabulary.

`get_info` accepts an optional `compact` boolean parameter, **default `true`**. In compact mode, empty `inputs`/`outputs` arrays and the `source` field are omitted from the functions list — this mostly reduces noise from inherited functions. Pass `compact: false` when you need to distinguish `"blueprint"` vs `"inherited"` sources or verify full parameter signatures (e.g., during BP→C++ migration analysis).
- **Structure:** `add_variable`, `remove_variable` (guarded: see Native member adoption), `add_function`, `get_class_defaults`, `set_class_defaults`, `configure_timeline`, `set_component_defaults`, `add_scs_component`, `remove_scs_component`, `rename_scs_component`
- **Class Settings:** `add_interface`, `remove_interface`, `set_tick_settings`, `set_replication_settings`
- **Migration:** `analyze_for_migration`, `cleanup_migration`, `remove_scs_component`, `rename_scs_component`, `recompile_dependents`, `fixup_redirectors`, `compare_blueprints`. `fixup_redirectors` is folder-wide and recursive by default and force-deletes unreferenced redirectors; the migration pipeline never calls it (see `resources/cpp-migration.md`). `remove_scs_component` and `rename_scs_component` always write the package; `rename_scs_component` also saves the dependents it touches.
- **Native member adoption (guarded, strict params, `dry_run` first):** `reparent`, `rename_member`, `adopt_native_member`, `adopt_scs_into_native`, `swap_scs_component_class`, plus guarded `remove_variable` and `cleanup_migration`. All take `dry_run`, an optional `expected_fingerprint` object (returned by a dry run), `compile` and `save` (`save` requires `compile`), and report `apply_status`, `compile_status`, `readback_status`, `rollback_status`, `save_status`. Params: `reparent` {`asset_path`, `new_parent`; `dry_run`, `expected_fingerprint`, `compile`, `save`, `acknowledged_collisions`, `report_path`}; `rename_member` {`asset_path`, `kind` (`variable`/`function`/`dispatcher`/`local`), `old`, `new`; `function`, `dry_run`, `expected_fingerprint`, `compile`, `save`, `acknowledged_losses`}; `adopt_native_member` {`asset_path`, `mappings` [`{bp_variable, native_property, default?}`]; `transfer_default`, `retarget_nodes`, `dry_run`, `expected_fingerprint`, `compile`, `save`, `acknowledged_losses`}; `adopt_scs_into_native` {`asset_path`, `mappings` [`{scs_node, native_component}`]; `copy`, `remove_scs`, `dry_run`, `expected_fingerprint`, `compile`, `save`, `acknowledged_losses`}; `swap_scs_component_class` {`asset_path`, `component_name`, `new_class`; `dry_run`, `expected_fingerprint`, `compile`, `save`, `acknowledged_losses`}; `remove_variable` {`asset_path`, `name`; `dry_run`, `expected_fingerprint`, `compile` (default false), `save` (default false), `remove_referencing_nodes`, `acknowledged_losses`}; `cleanup_migration` {`asset_path`; `new_parent_class`, `remove_variables`, `remove_functions`, `migrated_overrides`, `dry_run`, `expected_fingerprint`, `remove_referencing_nodes`, `acknowledged_collisions`, `acknowledged_losses`, `expected_cdo_values`, `compile`, `save`}. Error codes: `AMBIGUOUS_CLASS`, `INVALID_PARENT_CLASS`, `NAME_COLLISION`, `POTENTIAL_DATA_LOSS` (with `required_acknowledgment`), `MEMBER_REFERENCED`, `MISSING_PROPERTY_REDIRECT` (returns the `[CoreRedirects]` line), `READBACK_MISMATCH`, `STALE_PRECONDITION`. To move a variable into a native parent use `adopt_native_member`, not `remove_variable`/`cleanup_migration` (removal destroys the referencing nodes). Workflow and rules: `resources/cpp-migration.md`, "Guarded native member adoption".
- **Graph maintenance:** `delete_orphaned_nodes`, `remove_graph`, `search`
- **Text inventory and migration verification:** `export_text_inventory`, `export_snapshot`, `compare_snapshots`, `compile_all`
- **Project-wide analysis export:** `export_migration_analysis`

`export_snapshot(asset_path, out_path, sections?)` writes a deterministic migration snapshot to a file and returns only `asset_path`, `out_path`, `format_version` and `counts` (`variables[].default` is read from the CDO; `components` records this Blueprint's own overrides of inherited components; own SCS nodes carry `attached_to_inherited`); `compare_snapshots(before, after, report_path?)` diffs two snapshot files into `added`/`removed`/`changed`/`moved` per section (a CDO property whose declaring class changed with an equal value is `moved`, decided on the value alone with a `type_change` marker and float/double compared at float precision; an empty compared set and duplicate record keys are refused) and limits the inline report to 40000 characters (`RESPONSE_TOO_LARGE` — pass `report_path`). `compile_all(out_path, path_prefix | paths, types?)` compiles a folder or an explicit list through the single-asset compile (assets blocked after a failed recovery are skipped with a reason; one garbage collection at the end; synchronous, router window 1800 s), writes the per-asset report and returns `out_path`, `totals` and `first_failures`. All file paths must resolve under the project `Saved`, `Content` or `Config`.

`graph_metrics` (read-only; `asset_path`, optional `thresholds` `{max_nodes_per_entry: 10, max_nodes_per_blueprint: 30}`) measures only logic that can run. Scope: every ubergraph and function graph plus every interface-implementation graph, limited to K2-schema graphs (Widget Blueprint graphs included). AnimGraphs and state-machine graphs are skipped, producing no entries and no `unreachable` rows; macro graphs are never measured alone, only through their instances. An **entry** is a node with an exec output and no exec input (events, custom/bound/input events, Enhanced Input and debug-key nodes, function entries). A function entry is always live; other entries are live only when an exec output is linked. A **functional node** is reachable from a live entry by exec flow plus the backward data closure (for a function entry also seeded from its `FunctionResult` nodes), excluding the entry, `FunctionResult`, comments and reroutes; macro instances and collapsed nodes count as the functional nodes of their inner graph. The response has `has_tick` (true only for a live Tick), `totals` (`functional_nodes`, `unreachable_nodes`, `ghost_entries`, `entries`), `entries` (`graph`, `name`, `kind`, `node_id`, `live`, `functional_nodes`, `conditionals`, `variable_gets`, `max_getter_fanout`), `unreachable` (per graph, up to 50 node ids), `ghost_entries`, `thresholds`, and `violations` (`scope` entry or blueprint, with `limit`). Non-live entries report `functional_nodes: 0`. An oversized response is refused; use `analyze_for_migration` with `sections: ["complexity_metrics"]` for a bounded summary.

`analyze_for_migration` takes an optional `sections` array; omitted or empty means all. The identity fields (`name`, `asset_path`, `type`, `parent_class`, `native_parent_class`, `parent_class_path`) are always present. Valid sections: `is_compiled`, `variables`, `functions`, `scs_components`, `scs_collisions`, `dynamic_components`, `graphs`, `per_graph_elements`, `latent_nodes`, `timelines`, `event_dispatchers`, `interfaces_implemented`, `input_bindings`, `construction_script`, `widgets`, `named_slots`, `widget_animations`, `widget_bindings`, `referenced_user_types`, `cdo_overrides`, `instanced_subobjects`, `widget_dependencies`, `entity_summary`, `complexity_metrics`. An unknown name is refused with `INVALID_FIELD` before any output, and an oversized unselected analysis is refused with a suggestion to pass `sections`. `compare_blueprints` takes `sections` from `variables`, `functions`, `components`, `cdo`. On plugin builds that predate the #119 fix a Widget Blueprint can report an empty `widgets` array; read the tree with `umg_cmd(command="get_tree")` instead.

For a Widget Blueprint, `widgets` lists the full widget tree in pre-order, each row with `is_variable` and `bound_events_in_graph`; `entity_summary` keeps only the variable or event-bound widgets. Only `is_variable: true` widgets are BindWidget candidates.

`remove_graph` deletes a whole function, macro, extra event graph, or custom event through `blueprint_cmd(command="remove_graph")`; it is not `graph.apply_patch` or `blueprint_compose`. It requires strict boolean `dry_run`, `compile`, and `save`; optional strict `cascade_exec_chain` defaults to `false`. Preview (`dry_run=true`, `save=false`) returns `fingerprint_before` and `validation_hash`; apply requires both as `expected_fingerprint` and `expected_validation_hash`. `compile=false` never saves, and `save=true` requires `compile=true` and a clean starting package; EventGraph and ConstructionScript are protected. Full semantics: [CortexBlueprint system reference](https://github.com/etelyatn/CortexSandbox/blob/main/docs/systems/cortex-blueprint.md#guarded-graph-removal).

`export_text_inventory(asset_path, out_path?)` is a read-only inventory of every `FText` in a Blueprint: class defaults (recursing through structs/arrays/sets/maps), Widget Blueprint widgets, and every text pin default in every graph. Each entry carries `location` (`class_default`|`widget`|`pin`), `owner`, `path`, `value` and `source_kind` (`string_table`|`literal`|`culture_invariant`|`empty`, plus `table_id`/`key` for String Table entries); entries are sorted so before/after inventories diff line-by-line, and `counts` gives the total and per-`source_kind` numbers. The inline response is limited to 40000 characters. Larger inventories return `_error="RESPONSE_TOO_LARGE"`, `reader_complete=false`, `counts`, `max_response_chars` and a hint — nothing is trimmed silently. Pass `out_path` (a file under the project `Saved`, `Content` or `Config`) to write the full inventory JSON there; the response then contains only `asset_path`, `out_path` and `counts`. An unusable `out_path` (outside those roots, or otherwise unsafe) is refused before any asset work with the safe-file contract's own `INVALID_FILE_PATH`, the same code the Data file commands return.

`export_migration_analysis` analyzes many Blueprints in one call and writes the result to files: params `path_prefix` (a mounted content folder) **or** `paths` (array of asset paths) — exactly one —, optional `types` (the `blueprint_cmd` `list` vocabulary, case-insensitive), optional `sections` (the `analyze_for_migration` vocabulary plus `graph_metrics`; default is a migration-planning subset), and `out_path` (a file under the project `Saved`, `Content` or `Config`; anything else is refused with `INVALID_FILE_PATH` before any work). It writes JSONL, one `{asset_path, analysis, graph_metrics?}` per line (a failed asset is a row `{asset_path, error_code, error_message}`), atomically, plus `<out_path minus extension>.index.json` whose rows carry `name`, `asset_path`, `type`, `parent_class`, `native_parent_class`, `parent_chain` (Blueprint ancestors), `metrics` (`functional_nodes`, `has_tick`, `unreachable_nodes`, `conditionals`), `violations`, `migration_confidence`, `unsupported_node_types` and `blockers`. The response is a compact summary. A `path_prefix` request reports `totals.matched_assets` (Blueprints found before the `types` filter) and a `warnings` entry when the folder matched nothing. Index violations always use the default `graph_metrics` thresholds (10 nodes per entry, 30 per Blueprint) because the command has no `thresholds` parameter. Enumeration mirrors `compile_all`: exactly one of `path_prefix`/`paths`, level script Blueprints excluded, missing paths reported as rows, assets blocked by the mutation guard skipped with a reason. It reads and writes no asset state (it only writes the export files), is synchronous, and the MCP router waits up to 1800 s.

- **Level Blueprint:** No tool builds its path. Use the synthetic asset path `__level_bp__:<map_path>` (for example `__level_bp__:/Game/Maps/TestMap`) with `graph_cmd` commands. Save with `level_cmd(command="save_level")`, not `blueprint_cmd(command="save")`.

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

- `list_graphs`, `get_subgraph`, `search_nodes`, `trace_exec`, `trace_dataflow`, `list_event_handlers`, `find_event_handler`, `find_function_calls`, `describe_node`, `add_node`, `remove_node`, `connect`, `disconnect`, `set_pin_value`, `auto_layout`, `get_authoring_context`, `apply_patch`
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

Reviewed `retire_entries` additionally accepts an explicit closed `orphan_component_node_guids`
inventory of exact supported ordinary nodes. `entry_node_guids` may be omitted only for a nonempty
closed orphan inventory; an explicitly empty entry array is invalid, and `additional_node_guids`
still requires entries. VariableGet/Set require resolved class-owned properties; BreakStruct requires
a resolved reflected struct; exact ExecutionSequence and Select are admitted. External consumers,
subclasses and graph owners still refuse. Preview, exact approval, fingerprints, validation hash,
required compile/readback and explicit save remain mandatory; this is not arbitrary node deletion.

`list_graphs` returns user-visible Blueprint graphs. Top-level entries include `kind`
(`ubergraph`, `function`, `macro`, `delegate`, or `interface_impl`); `interface_impl`
entries also include `owning_interface`. Delegate graphs are readable but not mutable
through generic graph commands.

`list_graphs` accepts `include_subgraphs`; collapsed and macro subgraphs then appear with their `subgraph_path`.

`search_nodes` filters are all optional: `node_class`, `function_name`, `display_name`, `graph_name`, `subgraph_path`, `compact`. With no filter it returns every node (compact rows) in the selected scope, which is the paged node inventory. `graph_name` restricts to one graph (with `subgraph_path` for a subgraph); without it every graph is searched. `node_class` is case-insensitive and matches the node's class or any superclass name (a leading `U` is optional), so `K2Node` returns every K2 node; a trailing `*` is a prefix match on the runtime class name. Rows are in `results`, paged by the Python `limit` (1–200) and `cursor` mechanism.

`get_subgraph` takes `graph_name`, `subgraph_path`, `node_ids`, `include_edges`. A response over the 40,000-character ceiling is refused instead of shortened: select fewer `node_ids` or pass `include_edges: false`.

Generic read commands resolve graphs by name: if names collide across categories they resolve the
first match, so prefer unique names. Authoring does not rely on that resolution — a patch target is a
`graph_ref` carrying a canonical `graph_guid` (plus an optional `subgraph_path`) taken from
`graph.get_authoring_context`.

`auto_layout` — repositions node bodies using execution-first left-to-right layout with parameter grouping. `mode`: `"full"` repositions eligible non-comment nodes; `"incremental"` only repositions nodes at `(0,0)` while reserving established bodies without moving them. Optional `graph_name`, `horizontal_spacing`, `vertical_spacing`. To target a composite child, supply both the root `graph_name` and its dot-separated `subgraph_path`; a child path without a root is refused.

The response reports eligible `node_count`, `graphs_processed`, actual `changed_node_count`, and `unchanged`. A repeated unchanged layout does not dirty the asset. Layout never saves implicitly: use explicit asset persistence after inspection. Read graph/node data with `compact: false` to verify positions, and inspect the actual Blueprint Editor surface; a success response alone is not visual or save/reload proof.

### Compact Serialization (default for node reads)

`search_nodes` and `get_subgraph` serialize nodes compactly by default. `search_nodes` declares an optional `compact` boolean; `get_subgraph` reads the same `compact` flag in the native handler although it is not listed among its declared params. Compact mode strips fields AI agents rarely need, reducing response size on typical graphs.

| Command | `compact=true` strips |
|---------|----------------------|
| `search_nodes` | `node_class` (duplicate of `class`) — no positions in search results to begin with |
| `get_subgraph` | `position`, `node_class`, `pin_count`, hidden pins with no connections/defaults, `is_connected: false`, empty `default_value` |

**Pin skip predicate** (`get_subgraph` only): a pin is excluded only when ALL of `bHidden`, no `LinkedTo`, empty `DefaultValue`, empty `DefaultTextValue`, AND `DefaultObject == nullptr`. Hidden class-reference pins with meaningful defaults are preserved.

**Pass `compact: false` on `get_subgraph` when:**
- Debugging visual layout (need `position` x/y)
- Inspecting every hidden pin (e.g., tunnel boundaries, world-context pins)
- Generating C++ from a BP graph (migration correctness — Ground Truth Table needs full fidelity)
- Running asserts against field presence in tests

See `blueprint-patterns.md` for node class short names and full node type table.

---

## Material (`material_cmd`)

- **Asset:** `list_materials`, `get_material`, `create_material`, `delete_material`, `set_material_property`
- **Root inputs:** `set_material_input`
- **Instances:** `list_instances`, `get_instance`, `create_instance`, `delete_instance`
- **Parameters:** `list_parameters`, `get_parameter`, `set_parameter`, `set_parameters`, `reset_parameter`
- **Graph:** `list_nodes`, `get_node`, `add_node`, `remove_node`, `list_connections`, `connect`, `disconnect`, `auto_layout`, `set_node_property`, `get_node_pins`
- **Collections:** `list_collections`, `get_collection`, `create_collection`, `delete_collection`, `add_collection_parameter`, `remove_collection_parameter`, `set_collection_parameter`
- **Dynamic Instances (PIE):** `list_dynamic_instances`, `get_dynamic_instance`, `create_dynamic_instance`, `destroy_dynamic_instance`, `set_dynamic_parameter`, `get_dynamic_parameter`, `list_dynamic_parameters`, `set_dynamic_parameters`, `reset_dynamic_parameter`

`get_node` accepts an optional `properties` selector (array of non-empty property names). Omitted/empty
keeps the previous full editable read. A selected read keys `properties` by the requested selector and
validates the root segment against the same editable admission as the full read (a dotted path cannot
cross a non-editable root); an unknown or non-editable name refuses `PropertyNotFound`.

### Root input state

A root input (the `MaterialResult` pins) stores more than its connection: an output index, a channel
mask, and — for constant-capable types — an inline `use_constant`/`constant` pair. `get_material` and
`list_connections` expose that serialized state and `set_material_input` writes it. Do not inspect or
edit it through expression-node commands: root inputs live on the material, not on a node.

> Availability: these fields and `set_material_input` belong to the material input-state contract
> ([UnrealCortex #184](https://github.com/etelyatn/UnrealCortex/issues/184)) and require a plugin build
> that declares them. `core.get_operation_schema` against the connected editor is authoritative; an
> older build answers `UNKNOWN_COMMAND` for the command and omits the read fields rather than silently
> ignoring a patch.

`get_material` keeps `asset_path` and adds optional `include_input_state` (boolean, default `false`)
and `properties` (array of dotted reflected property paths). It always returns, beside the existing
fields: `effective_blend_mode` (same complete enum naming as `blend_mode`), the serialized
`can_masked_be_assumed_opaque` flag, and `warnings`. `sm6_warnings` remains its own established field.

`include_input_state=true` adds `root_inputs`, one record per available serialized root input —
including disconnected inputs — with these fields:

| Field | Meaning |
|---|---|
| `input` | Canonical property-derived name (`BaseColor`, `OpacityMask`, `CustomizedUVs0`, …) |
| `connected`, `source_node` | Current connection; `source_node` is `null` when disconnected |
| `output_index`, `mask`, `mask_r`, `mask_g`, `mask_b`, `mask_a` | Native stored output index and channel flags |
| `supports_constant` | The input type has an inline constant at all |
| `inline_constant_allowed` | Material Editor authoring policy for that input |
| `use_constant`, `constant` | Stored inline state; `null` when the type has no inline constant |

`use_constant: null` / `constant: null` is a capability statement, not a missing or unreadable field.
`supports_constant` is a type fact and `inline_constant_allowed` an editor authoring policy; neither is
a compiler-precedence claim. `constant` is never reinterpreted: scalar is a number, color is
`{r,g,b,a}`, vector3 is `{x,y,z}`, vector2 is `{x,y}`. Unsupported root inputs are absent, not invented.

`list_connections` accepts the same `include_input_state` flag and returns the identical `root_inputs`
projection beside `connections` and `count`. Edge enumeration stays connected-only: a disconnected
input appears in `root_inputs`, never as an edge.

Both extended reads are complete-or-refuse. An oversized projection returns `RESPONSE_TOO_LARGE` with
`reader_complete: false` and supported narrowing guidance (select fewer `properties`, omit
`include_input_state`, or read root state separately through `get_material`). These reads have no
`limit`/`offset` paging, and a partial `root_inputs`/`connections` array is never presented as complete.

### Writing root input state

`set_material_input` requires `asset_path` and `input`; the patch may contain any of `use_constant`,
`constant`, `output_index`, `mask`, `mask_r`, `mask_g`, `mask_b`, `mask_a`.

- At least one patch field is required. Omitted fields preserve current state; empty, `null`, or
  malformed values are refused, never treated as deletion.
- `input` matches the canonical `EMaterialProperty` names a read returns (`ShadingModel`,
  `CustomData0`, `CustomizedUVs0`, …); case, underscore and space differences are ignored
  (`custom_data_0`, `CustomizedUV0`). Accepted aliases are `ClearCoat` for canonical `CustomData0` and
  `ClearCoatRoughness` for canonical `CustomData1`; reads always report the canonical name. Any
  available serialized root input is addressable even when the material domain or blend mode leaves it
  inactive.
- The whole patch is validated and staged before any transaction or edit notification. Unknown/absent
  inputs, unknown fields, wrong types, non-finite or out-of-storage-range numbers, and invalid output
  indices refuse without changing values, other inputs, or dirty state.
- `constant`/`use_constant` require a constant-capable input; `use_constant: true` additionally
  requires `inline_constant_allowed`. Setting `use_constant: false` on a capable disabled-inline input
  is allowed.
- `output_index` requires a connected expression and a valid output on it. Changing it initializes the
  masks from that output; explicit mask fields in the same patch then override those defaults. Masks
  accept integer `0` or `1` only — other numbers are refused, not truncated.
- `use_constant: true` on a connected, allowed input is intentional state authoring, not an implicit
  disconnect. The connection stays, the read reports the resulting condition, and `warnings` may
  explain it.
- Color and vector constants are replaced as complete objects; scalar constants are plain numbers.
  There is no partial color/vector merge and no expression-object editing through this command.

The response is `asset_path`, `updated: true`, `input_state` (the read projection for that input), and
`warnings` using the same diagnostics as a read. No other input, node, or legacy blend override changes.
Root-input, property and rewire writes never save implicitly; persist with
`core_cmd(command="save_asset", ...)`.

```python
# scalar constant on a disconnected input (abridged response; no warning applies here)
material_cmd(command="set_material_input", params={
    "asset_path": "/Game/Materials/M_Simple",
    "input": "Metallic",
    "constant": 0.8,
    "use_constant": True,
})
# -> {"asset_path": "/Game/Materials/M_Simple", "updated": true,
#     "input_state": {"input": "Metallic", "connected": false,
#                     "use_constant": true, "constant": 0.8},
#     "warnings": []}

# typed constants
{"constant": {"r": 0.2, "g": 0.4, "b": 0.8, "a": 1.0}}   # color
{"constant": {"x": 0.0, "y": 1.0, "z": 0.5}}              # vector3
{"constant": {"x": 0.0, "y": 1.0}}                        # vector2
{"constant": 0.75}                                        # scalar

# select the second output of the connected texture and keep its mask
material_cmd(command="set_material_input", params={
    "asset_path": "/Game/Materials/M_Cutout",
    "input": "OpacityMask",
    "output_index": 1,
})
```

### Effective blend mode and warnings

`warnings` is response data (never UE warning logs) and never mutates the asset:

- `BLEND_MODE_MISMATCH` — authored `blend_mode` and `effective_blend_mode` disagree. The usual case is
  `bCanMaskedBeAssumedOpaque: true` on an authored Masked material: it is effectively Opaque.
- `CONNECTED_EXPRESSION_IGNORED` — a connected constant-capable input has `use_constant: true`, the
  legacy translator allows its inline constant, and the material is not using the new HLSL generator.
  The message names that legacy-translator condition instead of claiming universal precedence. The new
  translator prioritizes a valid connection, so the condition is not reported there. Root-input
  warnings include the `input` field.

Neither condition is repaired automatically on read or on an unrelated edit. Diagnose, repair
explicitly, then read again and save explicitly:

```python
# 1. diagnose the opaque override
material_cmd(command="get_material", params={"asset_path": "/Game/Materials/M_Cutout"})
# -> {"blend_mode": "Masked", "effective_blend_mode": "Opaque",
#     "can_masked_be_assumed_opaque": true,
#     "warnings": [{"code": "BLEND_MODE_MISMATCH", "message": "..."}]}

# 2. clear the override (top-level non-editable UPROPERTY authoring is preserved)
material_cmd(command="set_material_property", params={
    "asset_path": "/Game/Materials/M_Cutout",
    "property_name": "bCanMaskedBeAssumedOpaque",
    "value": False,
})

# 3. clear a legacy ignored connected constant instead, when that is the reported condition
material_cmd(command="set_material_input", params={
    "asset_path": "/Game/Materials/M_Cutout",
    "input": "OpacityMask",
    "use_constant": False,
})

# 4. confirm the warning cleared, then persist — input/property/rewire writes never save implicitly
material_cmd(command="get_material", params={"asset_path": "/Game/Materials/M_Cutout"})
core_cmd(command="save_asset", params={"asset_path": "/Game/Materials/M_Cutout"})
```

### Nested reflected properties

`set_material_property` keeps `asset_path`, `property_name`, `value`; `property_name` may now be a
dotted reflected path such as `EditorOnlyData.OpacityMask.UseConstant` or
`EditorOnlyData.OpacityMask.Constant`.

- The explicit `EditorOnlyData` prefix resolves through the material's editor-only data. The remaining
  struct/object hops must stay inside objects owned by this material through their Outer chain;
  referenced external assets refuse, and missing objects or null hops are neither created nor followed.
- Root-input leaf paths use the same validation and policy as `set_material_input`. Whole-input or
  `Expression` replacement through a generic path is refused — use `connect`/`disconnect`.
- Array indexing is not part of the path grammar. Use `set_material_input` for `CustomizedUVs0`..
  `CustomizedUVs7`; a path like `CustomizedUVs[0]` is not supported.
- Unknown or unsupported paths and failed conversions return `INVALID_FIELD` with the requested path
  and reason; any failed write preserves previous values and dirty state.

```python
material_cmd(command="get_material", params={
    "asset_path": "/Game/Materials/M_Cutout",
    "properties": ["EditorOnlyData.OpacityMask.UseConstant",
                   "EditorOnlyData.OpacityMask.Constant"],
})
# -> {"properties": {"EditorOnlyData.OpacityMask.UseConstant": false,
#                    "EditorOnlyData.OpacityMask.Constant": 1.0}, ...}

material_cmd(command="set_material_property", params={
    "asset_path": "/Game/Materials/M_Cutout",
    "property_name": "EditorOnlyData.OpacityMask.UseConstant",
    "value": False,
})
```

Selected reads key their projection under `properties` by the requested path and validate the whole
selector before returning anything — an invalid selector yields no partial projection. There is no
separate `get_material_property` command.

### Root connect and disconnect semantics

`connect` validates before the transaction, connects through the native expression input so the masks
match the selected output instead of retaining stale channels, and clears `use_constant` on that root
input. `disconnect` removes the expression, keeps `output_index: 0` and the stored constant, and
applies the Material Editor constant policy: inline constants are enabled for permitted
constant-capable inputs, `use_constant` is forced `false` for `WorldPositionOffset`, `Anisotropy`,
`PixelDepthOffset`, and `Displacement`, and nonconstant types are left without invented fields.
`Material` and `MaterialResult` are both accepted root aliases. Expression-to-expression disconnect is
not supported.

### Composites

- `material_compose` — atomic creation of a new Material with nodes and connections
- `material_instance_compose` — atomic creation of a new Material Instance with parameter overrides

---

## UMG (`umg_cmd`)

- **Tree:** `add_widget`, `remove_widget`, `reparent`, `get_tree`, `get_widget`, `list_widget_classes`, `duplicate_widget`, `set_widget_variable`, `rename_widget`
- **Properties:** `set_color`, `set_text`, `set_font`, `set_brush`, `set_padding`, `set_anchor`, `set_alignment`, `set_size`, `set_visibility`, `set_property`, `get_property`, `get_schema`
- **Animations:** `create_animation`, `list_animations`, `remove_animation`, `list_animation_bindings`, `ensure_animation_binding`, `set_animation_property_track`, `remove_animation_binding`
- **Migration reads (read-only):** `check_native_bindings`, `get_embedded_widget_values`, `get_commonui_info`

`get_widget` returns `render_transform`, `slot_type` (e.g. `"CanvasPanelSlot"`, `""` for the root) and `slot`. For every non-root widget `slot` is an object that always carries `type` (the slot class name) plus the typed layout summary (details vary by slot type) — never `null`, including slot classes without a summary such as ScrollBox or SizeBox. The root has `slot: null`.

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

Every non-`names_only` `get_tree` node also carries `is_variable` and, when the widget has a slot, `slot` (`type` plus the same typed layout summary `get_widget` builds; omitted for the root). Slot values are not part of the fingerprint, so there is no stale-write guard for slot-only edits. Nodes are larger than before, so fewer of them fit one response and trees that used to be read inline can now return `RESPONSE_TOO_LARGE`: for big screens read the hierarchy with `names_only=true` and `depth`/`max_nodes`, then fetch detail with `get_widget`.

`rename_widget(asset_path, widget_name, new_name, expected_fingerprint, scope?, dry_run?, expected_dependent_fingerprints?)` is a guarded Designer-widget rename with structural/skeleton refresh; it never compiles or saves (compile and save explicitly). `new_name` is used literally — no sanitizing, and case-only renames are refused. The default `scope="asset"` keeps the single-asset contract. `scope="dependents"` also renames the member references in child Blueprints and in Blueprints that reference the owner (discovered through the Asset Registry; unloaded assets are loaded). It is dry-run-first: `dry_run` defaults to `true` and returns the plan — `assets[]` with `asset_path`, `role` (`owner`|`child`|`referencer`), `fingerprint` and `references[]`, plus `conflicts[]` (a child anywhere below the owner that already declares `new_name` as a widget, member variable, component variable, timeline or function graph refuses the plan with `INVALID_OPERATION` before anything is dirtied — the engine would otherwise silently rename such a function graph, timeline or component variable in the child). To apply, send `dry_run=false` with the owner `expected_fingerprint` and `expected_dependent_fingerprints`, an object keyed by `asset_path` whose key set equals the plan's modified dependents exactly, each value being that dependent's plan fingerprint. Missing, extra or stale entries refuse with `STALE_PRECONDITION` before any mutation. A modified dependent that is blocked by the mutation guard refuses with `INVALID_OPERATION` naming the asset, before the transaction opens. References to UIComponent members the engine renames with the widget are scanned too. The apply is one transaction; if a reference to the old name survives the post-rename re-scan (or a dependent the plan listed without references was changed) the request fails and is really rolled back — the transaction is closed and undone, then the owner and every planned dependent are verified against their pre-request content and fingerprint, and original dirty flags are restored only for assets that verify. The error `details` report `rollback_status` (`restored`|`unverified`), `restored[]`, `blocked[]` (assets that could not be verified and are now blocked for further mutation), `remaining_references[]` and `unexpected_changes[]`. Inside a batch the request cannot undo the batch's transaction: it reports `rollback_status: "unverified"` and blocks every asset that is not provably unchanged. Dependents without references are not part of `expected_dependent_fingerprints`; the engine may mark one modified, which is reverted and re-verified. Touched packages are left dirty — save them explicitly. Renaming away from a name that satisfies a required `BindWidget` property of the native parent chain refuses with `INVALID_OPERATION` naming the property (for an optional binding it succeeds and the result has `unbinds_optional_bindwidget: true`). Renaming onto a compatible inherited `BindWidget` name is allowed; an incompatible type refuses.

`check_native_bindings(asset_path, native_class?)` compares the `BindWidget`/`BindWidgetAnim` members of a native `UserWidget` base (default: the Blueprint's parent class; pass `native_class` to check a prospective base before reparenting) against the Widget Blueprint. It returns `native_class`, a flat `bindings` array sorted by `kind` (`widget`|`animation`) then `name` — each record has `kind`, `name`, `optional`, `status`, `expected_class` and, where relevant, `actual_class` and `name_suggestion` — plus `counts` per status and `has_errors`. `status` is `matched`, `type_mismatch` (right name, incompatible class), `missing` (required, absent), `optional_missing`, or `not_transient` (a `BindWidgetAnim` without `Transient`, a compiler error). Names match case-sensitively; `name_suggestion` appears only for `missing`/`optional_missing`. A binding the compiler satisfies with the parent Widget Blueprint's same-named, compatible widget is `matched` for a child Widget Blueprint. Every record also has `referenced_by_graphs` (variable nodes in the checked Blueprint's own graphs that read or write that member; child Blueprints' graphs are not counted) and `blueprint_visible` (the native property is `BlueprintVisible`/`BlueprintReadOnly`/`BlueprintReadWrite`); a member that graphs reference while `blueprint_visible` is `false` is the reparent compile error "X is not blueprint visible" and is counted in `counts.not_blueprint_visible`. `has_errors` is true for any `missing`, `type_mismatch`, `not_transient` or not-blueprint-visible referenced member. It only reports — nothing is fixed.

`get_embedded_widget_values(asset_path, widget_name?)` reads the per-instance values of embedded `UserWidget`s (all of them, or the one named): editable, instance-editable properties declared below `UUserWidget` (Blueprint or native, so a variable moved to a native base stays visible). Each record has `property`, `declared_in`, `type`, `value` and `is_override` (differs from the class default); results are sorted by widget then property so they can be diffed before/after a move and after save/reload.

`get_commonui_info(asset_path)` reads CommonUI data for a Widget Blueprint (`commonui_bases`, `activatable` settings, implemented `overrides`, `buttons`, text/border styles, de-duplicated `style_assets`) or, for a CommonUI style Blueprint, `asset_kind: "style"`, `style_kind` and the referenced styles. When the CommonUI plugin is not loaded it returns `commonui_available: false` without an error — treat that as "no CommonUI data", not a failure.

`list_animation_bindings` returns canonical `FWidgetAnimationBinding` records, possessables, tracks, channels, and a version-2 content-guard `fingerprint`. Add `include_track_content: true` to include each supported float/color track's `property_path`, `type`, canonical evaluation state and sections/channels with per-channel `{frame_number, time_seconds, value, interpolation}`. A detailed page that exceeds the response ceiling returns `_error: "RESPONSE_TOO_LARGE"` with `reader_complete: false` and summary counts instead of a partial page; `pagination.is_complete` independently reports whether every binding was returned. `remove_animation_binding` surgically removes a single binding record by selector (`{widget_name, slot_widget_name, binding_guid, is_root_widget}`) using optimistic locking (`expected_fingerprint`), defaulting to `dry_run=true` and `save=false`. Shared MovieScene possessables and tracks are preserved. Renaming a Designer widget propagates its binding `WidgetName` and possessable name; a stale `expected_fingerprint` refuses with `STALE_PRECONDITION` and the current fingerprint, without mutation.

**Guarded animation authoring:** `ensure_animation_binding` creates or resolves the ordinary Designer-widget binding for `widget_name` (the flag stays `is_root_widget: false`; root-user-widget, slot and dynamic bindings are refused). `set_animation_property_track` creates, replaces or clears exactly one `float`, `FLinearColor` or `FSlateColor` property track on an existing binding, addressed by `selector`, `property_path` and a `track` object (`type` plus half-open `sections` with `time_seconds`/`value`/`interpolation` keys). Both color properties use `type: "color"` with linear RGBA keys. A section optionally accepts `completion_mode: "RestoreState"` (default) or `"KeepState"`; completion state is fingerprinted. `track: null` clears one property track while retaining the binding. Both commands require the full content-guard `fingerprint` from `list_animation_bindings` as `expected_fingerprint`, reject any supplied cursor/limit/offset field, default `dry_run` to `true`, and never compile or save. Limits: ordinary Designer widgets, at most 8 sections and 64 logical keys per track, and a 32,000-character prospective response budget. See `resources/umg-patterns.md` for the full workflow.

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

- `widget_compose` — atomic creation of a new UMG Widget Blueprint with an initial widget hierarchy; a
  `padding` dict in a widget spec is applied as the nested `padding` object on `umg.set_padding`

---

## Animation (`anim_cmd`)

- **Inspection:** `list_assets`, `get_sequence_info`, `get_montage_info`, `get_skeleton_info`, `get_animbp_info`
- **Guarded authoring:** named notifies, float curves, montage sections, skeleton sockets, object notifies, and notify states.
- Object notify selectors use `{ index, class_path, time }`; notify-state selectors also include `duration`.
- Every mutation requires `expected_fingerprint`, supports `dry_run`, and defaults `save` to `false`. Only live capabilities advertise authoring families; later-stage animation systems remain unavailable.

---

## Level (`level_cmd`)

- **Actors:** `spawn_actor`, `delete_actor`, `duplicate_actor`, `rename_actor`, `get_actor`, `set_transform`, `set_actor_property`, `get_actor_property`, `list_actors`, `find_actors`, `get_bounds`, `select_actors`, `get_selection`
- **Instance export:** `export_class_instances(class, maps, out_path, changed_only?)` writes every placed instance of an actor class (subclasses included) from saved maps without opening them (changed properties vs the class default, or all editable ones with `changed_only=false`, plus the archetype value; read-only/`EditConst` properties such as component references are excluded and instanced subobjects compare by content) and returns `out_path` and `totals`; World Partition maps are refused, other maps with external actor packages are read; only the persistent level is read (pass a streaming sublevel explicitly); packages a map pulls in stay loaded; synchronous (router window 1800 s)
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
blendspaces, retargeting, runtime preview, Sequencer, and Control Rig are out of scope. The anim domain has
no save command; use a mutation's `save=true` option, or `core.save_asset` where appropriate.

---

## Editor (`editor_cmd`)

- **PIE lifecycle:** `start_pie`, `stop_pie`, `get_pie_state`, `pause_pie`, `resume_pie`, `restart_pie`
- **Viewport:** `get_viewport_info`, `capture_screenshot`, `set_viewport_camera`, `focus_actor`, `set_viewport_mode`
- **Utilities:** `get_editor_state`, `get_recent_logs`, `execute_console_command`, `set_time_dilation`, `get_world_info`
- **Turnaround** (deferred; the router widens its receive window; the native server honours a per-command deferred timeout instead of its 30 s default): `live_coding_compile` (no params; patches only when Live Coding is already running, never starts it; blocks the editor until the patch is built, so transport timeouts must cover the compile — native bound 1800 s, router window 1830 s; new reflected types need a full build), `wait_ready` (`reopen_assets` array — a map path is refused and reported under `failed`; `timeout` seconds >0 and <=3600, default 120, the transport waits it plus a grace; conditions are Asset Registry loaded and no asset compilation pending — Blueprint compiles are synchronous and not observable; returns `ready`, `waited_seconds`, `opened`, `failed`, or `TIMEOUT`)
- **Input injection** (requires active PIE): `inject_key`, `inject_mouse`, `inject_input_action`, `inject_input_continuous`, `inject_input_sequence`

`inject_mouse` takes required `action: "click" | "move" | "scroll"`, optional numeric screen-space
`x`/`y` (current cursor by default), optional `button: "left" | "right" | "middle"` (default left
for click), and numeric `delta` required for scroll. It has no duration parameter or object-valued
delta. A handled Slate dispatch does not prove the intended UI control received a click.

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

QA no longer records or replays input. The legacy `start_recording`, `stop_recording`, `replay_session`
and `cancel_replay` commands were removed in the CortexReplay cutover; recorded physical-input
replay now lives in the `replay` domain (`cortex-replay` skill).

### Standalone

- `qa_test_step` — execute a single declarative QA test step (used by scenario runner)

`qa_test_step` and `scenario_compose` runs emit a per-step/summary `log_coverage` object
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

## Replay (`replay_cmd`)

Optional domain — registered only when live capabilities prove the editor exposes `replay`.
Human-captured physical-input recordings are discovered, started once, tracked and cancelled here;
recording, editing, permission and deletion are human-only in the CortexReplay window.

- `list_recordings` — live eligible recording page (ascending integer ID) with map, prerequisites and
  guard-coverage summary (no start pose — read `get_recording`'s `initial_state`); also returns
  `active_ai_run` and up to 100 `recent_ai_runs` terminal summaries from the last 24 hours. Paged
  with `after_recording_id` and `page_size` (1..100, default 20). Generic
  `limit`/`cursor`/`offset`/`page` are rejected.
- `get_recording` — one eligibility-checked recording's metadata, `initial_state` (recorded pawn
  transform, control rotation and viewport state) and `guard_coverage` counts. No input rows or
  arbitrary file access.
- `start_replay` — accept one AI run and return `run_id` plus `state: "Preparing"`. One-shot: never
  inside a Core batch and never automatically resent. Acceptance is not completion.
- `get_run` — live run state or retained terminal result (`Completed`, `Cancelled`, `Interrupted`,
  `Error`), dispatched/total event counts, completed/total frame counts, the admitted recording
  digests, `behind_seconds` (lag at the last paced frame), readiness-wait substate, guard/error details
  and `execution_error` (required for `Error`, present for `Cancelled`/`Interrupted` when the run has
  a cause).
- `cancel_replay` — request cancellation of that AI-originated run; returns `Finalizing` or the
  terminal state, so poll `get_run` until terminal.

After an unknown start outcome (`REPLAY_START_OUTCOME_UNKNOWN`), recover the admitted run through
`list_recordings`/`get_run`; never reissue start. Preparation and environment errors
(`EDITOR_BUSY`, `INCOMPATIBLE_PREREQUISITES`, `INPUT_PREPARATION_TIMEOUT`, …) are not gameplay
verdicts: use the table in [`resources/replay-workflow.md`](replay-workflow.md). Follow the
`cortex-replay` skill.

---

## Reflect

Reflect is reachable **two ways**:
- **Standalone MCP tools** (recommended, typed parameters): `query_class_hierarchy`,
  `query_class_detail`, `query_class_context`, `query_overrides`, `query_usages`,
  `get_dependencies`, `get_referencers`, `impact_analysis`, `rebuild_graph_cache`,
  `reflect_cache_status`, `scan_project`
- **The `reflect_cmd` router** for the native commands (`reflect.class_detail`,
  `reflect.class_hierarchy`, `reflect.search`, `reflect.find_overrides`, `reflect.find_usages`,
  `reflect.get_dependencies`, `reflect.get_referencers`, `reflect.find_broken_config_paths`,
  `reflect.export_dependency_graph`, `reflect.find_name_lookups`, `reflect.find_duplicate_graphs`)

Standalone tools and native commands are not interchangeable:

`query_class_detail` defaults to `detail="summary"` and accepts `summary|properties|full`, refusing an
unknown value client-side; it maps `properties` to a native `full` read plus a Python allowlist and
always injects `detail`. The **native** `reflect.class_detail` default is `full` and it accepts **only**
`summary`/`full` — anything else refuses `INVALID_FIELD` (`Invalid detail '<x>'; expected 'summary' or
'full'`) instead of degrading to the expensive full read. `summary` omits `properties`, `functions` and
`components`. Callers that previously passed an ad-hoc value such as `"name"` and silently got `full`
must now pass `summary`.

### Dependency map commands (project-wide, file-backed)

- **`get_referencers` and config.** `reflect.get_referencers` (and the standalone `get_referencers` tool) takes `asset_path`, `category`, `limit` and `include_config` (default `true`). INI references appear as rows `{package: <ini file>, type: "config", file, line, section, key}`; config rows are listed before asset rows and count toward `limit`, so a small `limit` keeps them, and `total`/`total_unfiltered` include them. The config scan reads `Config/*.ini` of the project (non-recursive) and of project plugins; it never reads `Saved/` or engine plugins.
- **`reflect_cmd` `find_broken_config_paths`** accepts no parameters. It checks every long package path and directory path in those INI files and returns `scanned_files`, `unreadable_files` (listed, never silently dropped), `checked` and `broken: [{file, line, section, key, value, path, kind}]`. A package token is broken when it neither is loaded nor exists on disk; a directory token when neither the Asset Registry nor the mapped disk directory has it.
- **`reflect_cmd` `export_dependency_graph`**: params `path_prefixes` (required array of mounted folders), `edge_kinds` (default all), `ordering_kinds` (default hard kinds) and `out_path` (required, under `Saved`/`Content`/`Config`). Edge kinds (from depends on to): `inherits`, `implements`, `calls_message`, `casts`, `spawns`, `creates_widget`, `widget_tree_child`, `listview_entry`, `level_placement` (the World asset hard-depends on the Blueprint package, or a hard referencer of its external-actor packages), `struct_use`, `enum_use`, `config`. Scheduled nodes are Blueprints, Worlds, user structs and user enums under the prefixes (`kind` `blueprint`/`world`/`struct`/`enum`); targets outside the prefixes (native `/Script/` classes, other content) are nodes flagged `external: true`, and ini files are `config_file` nodes; external, `asset` and config-file nodes are never scheduled. **Waves:** the graph over scheduled nodes is condensed into strongly connected components and each component is placed at its longest-path level, so everything a node depends on is in an earlier wave and every member of a cycle shares one wave. Only the hard kinds (`inherits`, `implements`, `struct_use`, `enum_use`, `widget_tree_child`, `listview_entry`) order the waves by default; soft kinds are still emitted as edges but order waves only when named in `ordering_kinds`. The file holds `{path_prefixes, edge_kinds, ordering_kinds, unresolved, nodes, edges: [{from, to, kind, graph?, widget?}], waves, cycles}` (plus `load_failures` when non-empty); `cycles` lists the components of size above 1. The response is `{out_path, nodes, edges_by_kind, waves: [sizes], cycles: <count>, ordering_kinds, unresolved, matched_assets, warnings}`. `unresolved` counts Blueprints with an unresolvable parent class and interface entries without a class instead of dropping them.
- **`reflect_cmd` `find_name_lookups`**: params `path_prefixes` (Blueprints to match against), optional `symbols`, optional `out_path`. It finds by-name access to Blueprint members that references cannot see: string-literal arguments of `FindFunction*`, `FindPropertyByName`, `FindFProperty`, `SetTimerByFunctionName`, `K2_SetTimer`, `CreateUFunction`, `BindUFunction` in the project's C++ (`Source/` of the game and project plugins) and Blueprint timer nodes with a literal function name. **It is literal-only:** a computed or concatenated name is not found, so an empty result is not proof of absence. Each hit is `{source: "cpp"|"blueprint", file|asset_path, line|node_id, api, name, matches}`; the result also reports `scanned_files`, `unreadable_files`, `matched_assets` and `warnings`. With `out_path` the full result goes to the file and the response is a compact summary (scalars plus the first 10 entries of each list and a `<name>_total` count).
- **`reflect_cmd` `find_duplicate_graphs`**: params `path_prefixes` (required), `min_nodes` (default 5), `similarity` (default 0.9) and optional `out_path`. **Exact groups are strict:** graphs with an identical normalised hash over node descriptors (class, member reference, non-default pin values, link topology; GUIDs, positions, comments and function local variables ignored). **Similar groups are loose:** graphs with the same name in different Blueprints whose descriptor multiset Jaccard is at least `similarity`, where references to other Blueprint classes collapse to their nearest native ancestor and Blueprint member references keep only the member name; those groups carry `loose: true`. Widget trees compare as `kind: "widget_tree"`. The response is `{exact_groups, similar_groups, blueprint_pairs: [{a, b, shared_graphs, widget_tree_similarity}], matched_assets, warnings}` sorted by size; with `out_path` the full result goes to the file and the response keeps the counts plus the first 10 of each list.

All new reflect commands accept only their declared parameters (an unknown one is refused with `INVALID_FIELD`), are read-only for assets, never save anything, and are synchronous with a 1800 s MCP router wait. An oversized inline response is refused with a suggestion to pass `out_path`.

### Other reflect read contracts

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
