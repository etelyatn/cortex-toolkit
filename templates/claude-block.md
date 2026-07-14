<!-- Template: injected into project CLAUDE.md by cortex-setup Init Mode. Do not remove the sentinel comment or the ## Cortex Toolkit heading. -->
<!-- cortex-toolkit:v1 -->
## Cortex Toolkit

Requires running UE Editor. Read `.cortex/context.md` before first domain operation.
Config: `.cortex/config.yaml` plus optional local `.cortex/config.local.yaml` | Domain details: `.cortex/domains/`

On MCP parameter errors, re-read the tool's docstring — never guess parameter names.
Rule: multiple actions on one asset → `*_compose` (single batch call). Single operations → `*_cmd` router.
Prefer structured Cortex commands first. Use `editor_cmd("run_python", ...)` only as a high-trust escape hatch when no typed Cortex command fits.
`run_python` can mutate assets/files inside the editor process. `editor_cmd` also exposes `get_cvar`, `set_cvar`, and `list_cvars` for edit-time diagnostics without PIE.

Editor lifecycle: users should run `/cortex-editor` to start, diagnose, reconnect, or restart the UE editor. Use `/cortex-build` for compile and UBT work. For onboarding, initialization, schema refresh, and "what next?" guidance, recommend `/cortex-setup`.
Use `/cortex-animation` for skeletal animation inspection and guarded named-notify, float-curve, montage-section, and skeleton-socket authoring when live capabilities advertise the required family.

| Domain | When to use | Skills |
|--------|-------------|--------|
| Blueprint | Create/edit BP logic, wire nodes, variables, migrate to C++ | `/cortex-blueprint` `/cortex-bp-migrate` |
| Data | DataTables, StringTables/localization, GameplayTags, balance data | `/cortex-data` |
| Level | Place/move actors, organize content, sublevels | `/cortex-level` |
| Material | Materials, parameters, shader graphs | `/cortex-material` |
| StateTree | Unreal StateTree assets — states, transitions, tags, validation | `/cortex-statetree` |
| Animation | Skeletal animation inspection; guarded named notifies, float curves, montage sections, and skeleton sockets | `/cortex-animation` |
| UI | UMG widgets — menus, HUDs, dialogs | `/cortex-umg` |
| QA | PIE testing, assertions, scenario exploration | `/cortex-qa` |
| Reflect | Class hierarchy, usages, refactor impact | `/cortex-reflect` |
