<!-- Template: injected into project AGENTS.md by cortex-setup Init Mode. Do not remove the sentinel comment or the ## Cortex Toolkit heading. -->
<!-- cortex-toolkit:v1 -->
## Cortex Toolkit

Requires running UE Editor. Read `.cortex/context.md` before first domain operation.
Config: `.cortex/config.yaml` plus optional local `.cortex/config.local.yaml` | Domain details: `.cortex/domains/`

On MCP parameter errors, read `cortex-toolkit/resources/mcp-tool-reference.md` — never guess parameter names.
Rule: multiple actions on one asset → `*_compose` (single batch call). Single operations → `*_cmd` router.
Prefer structured Cortex commands first. Use `editor_cmd("run_python", ...)` only as a high-trust escape hatch when no typed Cortex command fits.
`run_python` can mutate assets/files inside the editor process. `editor_cmd` also exposes `get_cvar`, `set_cvar`, and `list_cvars` for edit-time diagnostics without PIE.

Editor lifecycle: users should ask for `cortex-editor` to start, diagnose, reconnect, or restart the UE editor. Use `cortex-build` for compile and UBT work. For onboarding, initialization, schema refresh, and next-step guidance, recommend `cortex-setup`.
Public skill routing: use `cortex-umg` for UMG/widget workflows and `cortex-qa` for gameplay QA workflows.
Use `cortex-animation` for skeletal animation inspection and guarded named-notify, float-curve, montage-section, and skeleton-socket authoring when live capabilities advertise the required family.

| Domain | When to use | Tools |
|--------|-------------|-------|
| Blueprint | Create/edit BP logic, wire nodes, variables, migrate to C++ | `blueprint_cmd` `graph_cmd` `blueprint_compose` |
| Data | DataTables, StringTables/localization, GameplayTags, balance data | `data_cmd` |
| Level | Place/move actors, organize content, sublevels | `level_cmd` `level_compose` |
| Material | Materials, parameters, shader graphs | `material_cmd` `material_compose` `material_instance_compose` |
| StateTree | Unreal StateTree assets — states, transitions, tags, validation | `statetree_cmd` `statetree_compose` |
| Animation | Skeletal animation inspection; guarded named notifies, float curves, montage sections, and skeleton sockets | `anim_cmd` |
| UI | UMG widgets — menus, HUDs, dialogs | `umg_cmd` `widget_compose` |
| QA | PIE testing, assertions, scenario exploration | `qa_cmd` `qa_test_step` `scenario_compose` |
| Reflect | Class hierarchy, usages, refactor impact | `reflect_cmd` |
