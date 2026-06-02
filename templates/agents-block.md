<!-- Template: injected into project AGENTS.md by cortex-init Step 6. Do not remove the sentinel comment or the ## Cortex Toolkit heading. -->
<!-- cortex-toolkit:v1 -->
## Cortex Toolkit

Requires running UE Editor. Read `.cortex/context.md` before first domain operation.
Config: `.cortex/config.yaml` plus optional local `.cortex/config.local.yaml` | Domain details: `.cortex/domains/`

On MCP parameter errors, read `cortex-toolkit/resources/mcp-tool-reference.md` — never guess parameter names.
Rule: multiple actions on one asset → `*_compose` (single batch call). Single operations → `*_cmd` router.

Editor lifecycle: users should ask for `cortex-editor` to start/verify the UE editor and `cortex-status` for MCP/domain health. After init or structural content changes, recommend `cortex-schema-refresh` to regenerate `.cortex/schema/`. Agents may use `editor_cmd` for editor/PIE interaction and `core_cmd` for asset lifecycle operations.

| Domain | When to use | Tools |
|--------|-------------|-------|
| Blueprint | Create/edit BP logic, wire nodes, variables, migrate to C++ | `blueprint_cmd` `graph_cmd` `blueprint_compose` |
| Data | DataTables, StringTables/localization, GameplayTags, balance data | `data_cmd` |
| Level | Place/move actors, organize content, sublevels | `level_cmd` `level_compose` |
| Material | Materials, parameters, shader graphs | `material_cmd` `material_compose` `material_instance_compose` |
| StateTree | Unreal StateTree assets — states, transitions, tags, validation | `statetree_cmd` `statetree_compose` |
| UI | UMG widgets — menus, HUDs, dialogs | `umg_cmd` `widget_compose` |
| QA | PIE testing, assertions, scenario exploration | `qa_cmd` `qa_test_step` `scenario_compose` |
| Reflect | Class hierarchy, usages, refactor impact | `reflect_cmd` |
