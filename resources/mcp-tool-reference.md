# MCP Tool Reference

Flat catalog of all UnrealCortex MCP tools organized by domain.

## Tool Architecture

Tools fall into three categories:
- **Routers (10):** `core_cmd`, `data_cmd`, `blueprint_cmd`, `graph_cmd`, `level_cmd`, `material_cmd`, `umg_cmd`, `qa_cmd`, `reflect_cmd`, `editor_cmd` — dispatch named commands to existing assets
- **Composites (6):** `blueprint_compose`, `material_compose`, `material_instance_compose`, `widget_compose`, `level_compose`, `scenario_compose` — atomic creation of new assets in a single batch round-trip
- **Standalone (3):** `editor_restart`, `schema_generate`, `qa_test_step`

Rule: New asset creation → composite. Modifications to existing assets → router.

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
- **GameplayTags:** `list_gameplay_tags`, `validate_gameplay_tag`, `register_gameplay_tag`, `register_gameplay_tags`, `resolve_tags`
- **DataAssets:** `list_data_assets`, `get_data_asset`, `update_data_asset`
- **CurveTables:** `list_curve_tables`, `get_curve_table`, `update_curve_table_row`
- **StringTables:** `list_string_tables`, `get_translations`, `set_translation`
- **Search:** `search_assets`

---

## Blueprint (`blueprint_cmd`)

- **Assets:** `create_blueprint`, `list_blueprints`, `get_blueprint_info`, `delete_blueprint`, `duplicate_blueprint`, `compile_blueprint`, `save_blueprint`
- **Structure:** `add_blueprint_variable`, `remove_blueprint_variable`, `add_blueprint_function`
- **Level Blueprint:** `get_level_blueprint(map_path)` — returns synthetic `__level_bp__:/Game/Maps/MapName` path for use with all `graph_*` and `bp.*` commands; save Level Blueprint changes with `save_level`, not `save_blueprint` (returns `LevelBlueprintSaveError`)

### Composite

- `blueprint_compose` — atomic creation of a new Blueprint with variables, functions, and initial graph nodes

---

## Graph (`graph_cmd`)

- `graph_list_graphs`, `graph_list_nodes`, `graph_get_node`, `graph_add_node`, `graph_remove_node`, `graph_connect`, `graph_disconnect`, `graph_set_pin_value`, `graph_auto_layout`

`graph_auto_layout` — repositions nodes using execution-first left-to-right layout with parameter grouping. `mode`: `"full"` repositions all nodes; `"incremental"` only repositions nodes at position (0,0). Optional `graph_name`, `horizontal_spacing`, `vertical_spacing`.

See `blueprint-patterns.md` for node class short names and full node type table.

---

## Material (`material_cmd`)

- **Asset:** `create_material`, `delete_material`, `list_materials`, `get_material_info`, `save_material`
- **Graph:** `add_node`, `remove_node`, `list_nodes`, `get_node`, `connect`, `disconnect`, `set_node_property`, `auto_layout`
- **Instances:** `create_instance`, `list_instances`, `get_instance`, `set_instance_parameter`

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

- **Actors:** `spawn_actor`, `delete_actor`, `list_actors`, `get_actor`, `set_actor_transform`, `find_actors`
- **Organization:** `set_actor_label`, `set_actor_folder`, `list_folders`
- **Level management:** `load_level`, `save_level`, `list_levels`

### Composite

- `level_compose` — atomic placement of multiple actors with transforms in a single batch

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

- **World queries:** `get_world_state`, `find_actor`, `get_actor_properties`, `query_actors`
- **Game actions:** `move_to`, `interact`, `assert_condition`
- **Scenario engine:** `run_scenario`, `get_scenario_status`

### Standalone

- `qa_test_step` — execute a single declarative QA test step (used by scenario runner)

### Composite

- `scenario_compose` — atomic creation of a new QA scenario asset

---

## Reflect (`reflect_cmd`)

- `query_class_hierarchy`, `query_class_detail`, `query_class_context`, `query_overrides`, `query_usages`
- `get_dependencies`, `get_referencers`, `impact_analysis`
- `rebuild_graph_cache`, `reflect_cache_status`, `scan_project`

---

## Convention

Resources use full router syntax: `domain_cmd(command="name", params={...})`. Agent `.md` files use bare command names (e.g., `list_blueprints`) for readability.
