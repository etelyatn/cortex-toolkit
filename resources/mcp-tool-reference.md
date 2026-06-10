# MCP Tool Reference

Flat catalog of all UnrealCortex MCP tools organized by domain.

## Tool Architecture

Tools fall into three categories:
- **Routers (11):** `core_cmd`, `data_cmd`, `blueprint_cmd`, `graph_cmd`, `level_cmd`, `material_cmd`, `umg_cmd`, `qa_cmd`, `reflect_cmd`, `editor_cmd`, `statetree_cmd` — dispatch named commands to existing assets
- **Composites (7):** `blueprint_compose`, `material_compose`, `material_instance_compose`, `widget_compose`, `level_compose`, `scenario_compose`, `statetree_compose` — declarative creation workflows, with some composites also supporting update-mode orchestration
- **Standalone (3):** `editor_restart`, `schema_generate`, `qa_test_step`

Rule: New asset creation → composite. Isolated edits to existing assets → router. Multi-step or structure-wide updates to existing assets can use composite update mode.

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

---

## Response Handling

### Large Responses — Auto-Truncation

When a response exceeds 40KB, the MCP layer finds the largest list with 10+ items, binary-searches for the max item count that fits, and returns `_truncated` metadata:

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

### Pagination

All list commands support opt-in cursor-based pagination via two parameters:

- **`limit`** (integer, 1–200) — triggers pagination; returns first page with `_pagination` metadata
- **`cursor`** — opaque token from `_pagination.next_cursor`; returns next page without re-calling C++

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

### Error Codes

| Code | Meaning | Recovery |
|------|---------|----------|
| `RESPONSE_TOO_LARGE` | Response too large, no truncatable list found | Add filters or use `fields` param |
| `INVALID_LIMIT` | `limit` not an integer in [1, 200] | Pass an integer in range |
| `INVALID_CURSOR` | Cursor token is malformed | Restart pagination with `limit` |
| `CURSOR_EXPIRED` | Cached results expired (60s TTL) | Re-send original command with `limit` |

---

## Core (`core_cmd`)

- `get_status` — connection health, registered domains, engine/plugin versions
- `get_data_catalog` — unified project data overview (cached 10 min)
- `refresh_cache` — clear all cached MCP responses
- `schema_status` — check if `.cortex/schema/` exists, per-domain freshness and version (no editor required)
- `batch` — execute multiple commands sequentially with `$ref` resolution; see `resources/batch-pipeline-guide.md`
- `batch_query` — run multiple read queries in one round-trip; returns a keyed result map
- `switch_editor` — select target editor by PID or index when multiple editors are running
- `shutdown` — graceful editor shutdown

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
- **Raw file exports:** `export_datatable_json`, `export_string_table_json`, `export_data_assets_json`, `export_bulk_json`
- **Snapshot diff:** `compare_data_json`
- **File-backed imports:** `apply_import_ops_json`
- **GameplayTags:** `list_gameplay_tags`, `validate_gameplay_tag`, `register_gameplay_tag`, `register_gameplay_tags`, `resolve_tags`
- **DataAssets:** `list_data_assets`, `get_data_asset`, `update_data_asset`
- **CurveTables:** `list_curve_tables`, `get_curve_table`, `update_curve_table_row`
- **StringTables:** `list_string_tables`, `get_translations`, `set_translation`, `update_string_table`
- **Search:** `search_assets`

For large or repeatable data migrations, use raw export commands for large reads, `compare_data_json` when you need a deterministic exported-snapshot diff, and `apply_import_ops_json` for the corresponding file-backed write phase. Small targeted edits should still use direct mutation commands.

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

---

## Blueprint (`blueprint_cmd`)

- **Assets:** `create`, `list`, `get_info`, `delete`, `duplicate`, `compile`, `save`, `rename`, `reparent`

`get_info` accepts an optional `compact` boolean parameter, **default `true`**. In compact mode, empty `inputs`/`outputs` arrays and the `source` field are omitted from the functions list — this mostly reduces noise from inherited functions. Pass `compact: false` when you need to distinguish `"blueprint"` vs `"inherited"` sources or verify full parameter signatures (e.g., during BP→C++ migration analysis).
- **Structure:** `add_variable`, `remove_variable`, `add_function`, `get_class_defaults`, `set_class_defaults`, `configure_timeline`, `set_component_defaults`, `add_scs_component`, `remove_scs_component`, `rename_scs_component`
- **Class Settings:** `add_interface`, `remove_interface`, `set_tick_settings`, `set_replication_settings`
- **Migration:** `analyze_for_migration`, `cleanup_migration`, `remove_scs_component`, `rename_scs_component`, `recompile_dependents`, `fixup_redirectors`, `compare_blueprints`
- **Graph maintenance:** `delete_orphaned_nodes`, `search`
- **Level Blueprint:** Use `get_level_blueprint(map_path)` (standalone tool) to get a synthetic path, then use `graph_cmd` commands. Save with `level_cmd(command="save_level")`, not `blueprint_cmd(command="save")`.

### Composite

- `blueprint_compose` — atomic creation of a new Blueprint with variables, functions, and initial graph nodes

---

## Graph (`graph_cmd`)

- `list_graphs`, `list_nodes`, `get_node`, `search_nodes`, `add_node`, `remove_node`, `connect`, `disconnect`, `set_pin_value`, `auto_layout`

`list_graphs` returns user-visible Blueprint graphs. Top-level entries include `kind`
(`ubergraph`, `function`, `macro`, `delegate`, or `interface_impl`); `interface_impl`
entries also include `owning_interface`. Delegate graphs are readable but not mutable
through generic graph commands.

Graph targeting is currently name-based. If graph names collide across categories,
commands resolve the first matching graph. Prefer unique graph names until a stable
`graph_ref` or graph-kind disambiguator exists.

`auto_layout` — repositions nodes using execution-first left-to-right layout with parameter grouping. `mode`: `"full"` repositions all nodes; `"incremental"` only repositions nodes at position (0,0). Optional `graph_name`, `horizontal_spacing`, `vertical_spacing`.

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

### Composites

- `material_compose` — atomic creation of a new Material with nodes and connections
- `material_instance_compose` — atomic creation of a new Material Instance with parameter overrides

---

## UMG (`umg_cmd`)

- **Tree:** `add_widget`, `remove_widget`, `reparent`, `get_tree`, `get_widget`, `list_widget_classes`, `duplicate_widget`
- **Properties:** `set_color`, `set_text`, `set_font`, `set_brush`, `set_padding`, `set_anchor`, `set_alignment`, `set_size`, `set_visibility`, `set_property`, `get_property`, `get_schema`
- **Animations:** `create_animation`, `list_animations`, `remove_animation`

`get_widget` returns `render_transform`, `slot_type` (e.g. `"CanvasPanelSlot"`, `null` for root), and `slot` (layout details vary by slot type).

### Composite

- `widget_compose` — atomic creation of a new UMG Widget Blueprint with an initial widget hierarchy

---

## Level (`level_cmd`)

- **Actors:** `spawn_actor`, `delete_actor`, `duplicate_actor`, `rename_actor`, `get_actor`, `set_transform`, `set_actor_property`, `get_actor_property`, `list_actors`, `find_actors`, `get_bounds`, `select_actors`, `get_selection`
- **Components:** `list_components`, `add_component`, `remove_component`, `get_component_property`, `set_component_property`
- **Discovery:** `list_actor_classes`, `list_component_classes`, `describe_class`
- **Organization:** `attach_actor`, `detach_actor`, `set_tags`, `set_folder`, `group_actors`, `ungroup_actors`
- **Level management:** `get_info`, `list_sublevels`, `load_sublevel`, `unload_sublevel`, `set_sublevel_visibility`, `list_data_layers`, `set_data_layer`, `save_level`, `save_all`

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

## Editor (`editor_cmd`)

- **PIE lifecycle:** `start_pie`, `stop_pie`, `get_pie_state`, `pause_pie`, `resume_pie`, `restart_pie`
- **Viewport:** `get_viewport_info`, `capture_screenshot`, `set_viewport_camera`, `focus_actor`, `set_viewport_mode`
- **Utilities:** `get_editor_state`, `get_recent_logs`, `execute_console_command`, `set_time_dilation`, `get_world_info`
- **Input injection** (requires active PIE): `inject_key`, `inject_input_sequence`

See `qa-patterns.md` for input injection documentation.

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

### Composite

- `scenario_compose` — atomic creation of a new QA scenario asset

---

## Reflect

Reflect has **standalone MCP tools** (not accessed through `reflect_cmd`):
- `query_class_hierarchy`, `query_class_detail`, `query_class_context`, `query_overrides`, `query_usages`
- `get_dependencies`, `get_referencers`, `impact_analysis`
- `rebuild_graph_cache`, `reflect_cache_status`, `scan_project`

---

## Convention

Resources use full router syntax: `domain_cmd(command="name", params={...})`. Agent `.md` files use bare command names (e.g., `list`) for readability.
