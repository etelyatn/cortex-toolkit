<!-- Template: injected into project CLAUDE.md by cortex-setup Init Mode. Do not remove the sentinel comment or the ## Cortex Toolkit heading. -->
<!-- cortex-toolkit:v1 -->
## Cortex Toolkit

Requires running UE Editor. Read `.cortex/context.md` before first domain operation.
Config: `.cortex/config.yaml` plus optional local `.cortex/config.local.yaml` | Domain details: `.cortex/domains/`

On MCP parameter errors, re-read the tool's docstring — never guess parameter names.
Rule: multiple actions on one asset → `*_compose` (single batch call). Single operations → `*_cmd` router.

Editor lifecycle: users should run `/cortex-editor` to start, diagnose, reconnect, or restart the UE editor. Use `/cortex-build` for compile and UBT work. For onboarding, initialization, schema refresh, and "what next?" guidance, recommend `/cortex-setup`.

| Domain | When to use | Skills |
|--------|-------------|--------|
| Blueprint | Create/edit BP logic, wire nodes, variables, migrate to C++ | `/cortex-blueprint` `/cortex-bp-migrate` |
| Data | DataTables, StringTables/localization, GameplayTags, balance data | `/cortex-data` |
| Level | Place/move actors, organize content, sublevels | `/cortex-level` |
| Material | Materials, parameters, shader graphs | `/cortex-material` |
| StateTree | Unreal StateTree assets — states, transitions, tags, validation | `/cortex-statetree` |
| UI | UMG widgets — menus, HUDs, dialogs | `/cortex-umg` |
| QA | PIE testing, assertions, scenario exploration | `/cortex-qa` |
| Reflect | Class hierarchy, usages, refactor impact | `/cortex-reflect` |
