<!-- Template: injected into project CLAUDE.md or AGENTS.md by cortex-init Step 6. Do not remove the sentinel comment or the ## Cortex Toolkit heading. -->
<!-- cortex-toolkit:v2 -->
## Cortex Toolkit

Requires running UE Editor. Read `.cortex/context.md` before first domain operation.
Config: `.cortex/config.yaml` plus optional local `.cortex/config.local.yaml` | Domain details: `.cortex/domains/`

On MCP parameter errors, re-read the tool's docstring — never guess parameter names.
Rule: multiple actions on one asset -> `*_compose` (single batch call). Single operations -> `*_cmd` router.

Editor lifecycle: load the `cortex-editor` skill to start/verify the UE editor and `cortex-status` for MCP/domain health. After init or structural content changes, load `cortex-schema-refresh` to regenerate `.cortex/schema/`. The AI may use `editor_cmd` for editor/PIE interaction and `core_cmd` for asset lifecycle operations.

| Domain | When to use | Skills | Key MCP Tools |
|--------|-------------|--------|---------------|
| Blueprint | Create/edit BP logic, wire nodes, variables, migrate to C++ | `cortex-blueprint` `cortex-bp-migrate` | `blueprint_cmd` `graph_cmd` `blueprint_compose` |
| Data | DataTables, GameplayTags, balance data | `cortex-data` | `data_cmd` |
| Level | Place/move actors, organize content, sublevels | `cortex-level` | `level_cmd` `level_compose` |
| Material | Materials, parameters, shader graphs | `cortex-material` | `material_cmd` `material_compose` `material_instance_compose` |
| StateTree | Unreal StateTree assets — states, transitions, tags, validation | `cortex-statetree` | `statetree_cmd` `statetree_compose` |
| UI | UMG widgets — menus, HUDs, dialogs | `cortex-ui` | `umg_cmd` `widget_compose` |
| QA | PIE testing, assertions, scenario exploration | `cortex-qa-init` `cortex-qa-interactive` `cortex-qa-run` | `qa_cmd` `qa_test_step` `scenario_compose` |
| Reflect | Class hierarchy, usages, refactor impact | `cortex-reflect` | `reflect_cmd` |
