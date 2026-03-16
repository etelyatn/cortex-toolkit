<!-- Template: injected into project AGENTS.md by cortex-init Step 6. Do not remove the sentinel comment or the ## Cortex Toolkit heading. -->
<!-- cortex-toolkit:v1 -->
## Cortex Toolkit

AI-powered UE development via UnrealCortex MCP (`cortex_mcp` server, configured in `.mcp.json`).
Config: `.cortex/config.yaml` | Context: `.cortex/context.md` | Domain details: `.cortex/domains/`

Unreal Editor must be running before using tools. Call `core_cmd(command="get_status")` first — if it fails, the editor is not running; open it and retry.

| Domain | Use when you need to... | Key tools |
|--------|-------------------------|-----------|
| Blueprint | ...create/edit BP logic, wire nodes, add variables, migrate to C++ | `blueprint_cmd` `graph_cmd` `blueprint_compose` |
| Data | ...create/query DataTables, balance data, manage GameplayTags | `data_cmd` |
| Level | ...place/move actors, organize level content, stream sublevels | `level_cmd` `level_compose` |
| Material | ...create/edit materials, tune parameters, build shader graphs | `material_cmd` `material_compose` `material_instance_compose` |
| UI | ...build menus, HUDs, dialogs, or any UMG widget screen | `umg_cmd` `widget_compose` |
| QA | ...run gameplay tests in PIE, assert game state, explore scenarios | `qa_cmd` `qa_test_step` `scenario_compose` |
| Reflect | ...scan class hierarchy, find usages, analyze refactor impact | `reflect_cmd` |
