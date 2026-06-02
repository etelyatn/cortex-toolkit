<!-- Template: injected into project CLAUDE.md by cortex-init Step 6. Do not remove the sentinel comment or the ## Cortex Toolkit heading. -->
<!-- cortex-toolkit:v1 -->
## Cortex Toolkit

Requires running UE Editor. Read `.cortex/context.md` before first domain operation.
Config: `.cortex/config.yaml` plus optional local `.cortex/config.local.yaml` | Domain details: `.cortex/domains/`

On MCP parameter errors, re-read the tool's docstring — never guess parameter names.
Rule: multiple actions on one asset → `*_compose` (single batch call). Single operations → `*_cmd` router.

Editor lifecycle: users should run `/cortex-editor` to start/verify the UE editor and `/cortex-status` for MCP/domain health. After init or structural content changes, recommend `/cortex-schema-refresh` to regenerate `.cortex/schema/`. Agents may use `editor_cmd` for editor/PIE interaction and `core_cmd` for asset lifecycle operations.

| Domain | When to use | Skills |
|--------|-------------|--------|
| Blueprint | Create/edit BP logic, wire nodes, variables, migrate to C++ | `/cortex-blueprint` `/cortex-bp-migrate` |
| Data | DataTables, StringTables/localization, GameplayTags, balance data | `/cortex-data` |
| Level | Place/move actors, organize content, sublevels | `/cortex-level` |
| Material | Materials, parameters, shader graphs | `/cortex-material` |
| StateTree | Unreal StateTree assets — states, transitions, tags, validation | `/cortex-statetree` |
| UI | UMG widgets — menus, HUDs, dialogs | `/cortex-ui` |
| QA | PIE testing, assertions, scenario exploration | `/cortex-qa-init` `/cortex-qa-interactive` `/cortex-qa-run` |
| Reflect | Class hierarchy, usages, refactor impact | `/cortex-reflect` |
