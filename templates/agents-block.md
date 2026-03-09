<!-- Template: injected into project AGENTS.md by cortex-init Step 6. Do not remove the sentinel comment or the ## Cortex Toolkit heading. -->
<!-- cortex-toolkit:v1 -->
## Cortex Toolkit

AI-powered UE development via UnrealCortex MCP (`cortex_mcp` server, configured in `.mcp.json`).
Config: `.cortex/config.yaml` | Context: `.cortex/context.md` | Domain details: `.cortex/domains/{domain}.md`

Unreal Editor must be running before using tools. Call `get_status` first — if it fails, the editor is not running; open it and retry.

| Domain | Use when you need to... | Key tools |
|--------|-------------------------|-----------|
| Blueprint | ...create/edit BP logic, wire nodes, add variables, migrate to C++ | `get_blueprint_info` `compile_blueprint` `graph_add_node` `graph_connect` |
| Data | ...create/query DataTables, balance data, manage GameplayTags | `list_datatables` `get_datatable_row` `query_datatable` `add_datatable_row` |
| Level | ...place/move actors, organize level content, stream sublevels | `list_actors` `spawn_actor` `set_transform` `set_folder` |
| Material | ...create/edit materials, tune parameters, build shader graphs | `get_material` `create_material` `connect_material_nodes` `create_instance` |
| UI | ...build menus, HUDs, dialogs, or any UMG widget screen | `get_widget` `create_widget_screen` `set_text` `add_widget` |
| QA | ...run gameplay tests in PIE, assert game state, explore scenarios | `run_scenario_inline` `assert_game_state` `observe_game_state` |
| Reflect | ...scan class hierarchy, find usages, analyze refactor impact | `query_class_hierarchy` `query_usages` `impact_analysis` |
