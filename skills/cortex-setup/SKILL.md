---
name: cortex-setup
description: Use when setting up Cortex for a project, getting started, refreshing schema, or asking what to do next
---

# Cortex Setup

Public entrypoint for onboarding, project initialization, schema refresh, and guided next-step discovery.

## Intent Routing

- Initialization intent: "set up Cortex", ".cortex is missing", "configure MCP" -> Init Mode
- Guided start intent: "get started", "first time", "walk me through this" -> Onboarding Mode
- Schema intent: "refresh schema", "regenerate schema", "data structures changed" -> Schema Refresh Mode
- Help intent: "what should I do next?", "what can I do?", "help" -> Discovery Mode

Do not ask the user to choose internal mode names when the request already makes the route obvious.

## Init Mode

Set up the project for UnrealCortex.

1. Validate that `UnrealCortex.uplugin` exists under `Plugins/UnrealCortex/`, `Plugins/Developer/UnrealCortex/`, or another `Plugins/**/UnrealCortex.uplugin` path.
2. Find the `.uproject` file and verify `UnrealCortex` is not explicitly disabled in its `Plugins` array.
3. Detect the Unreal Engine install from common paths or `UE_PATH`. If still unknown, ask the user for the engine path.
4. Read the plugin's module list and map enabled domains:
   - `CortexData` -> `data`
   - `CortexBlueprint` + `CortexGraph` -> `blueprint`
   - `CortexMaterial` -> `material`
   - `CortexUMG` -> `umg`
   - `CortexLevel` -> `level`
   - `CortexQA` -> `qa`
   - `CortexReflect` -> `reflect`
   - `CortexStateTree` -> `statetree`
   - `CortexAnimation` -> `anim`
5. Create `.cortex/config.yaml`, `.cortex/context.md`, and `.cortex/domains/*.md` for detected domains. Ensure `.gitignore` contains `.cortex/config.local.yaml`.
 6. Create or update `.mcp.json` so `mcpServers.cortex_mcp` runs `uv run --directory {plugin_root}/MCP cortex-mcp` with `CORTEX_PROJECT_DIR={project_root}`.
 7. If the user works in OpenCode, ask whether to configure OpenCode. If yes, read the project's `opencode.json` (or start from `{}`), preserve all existing top-level keys and all existing `mcp` entries, and upsert:
    - the `cortex_mcp` MCP entry — same command and `CORTEX_PROJECT_DIR` as `.mcp.json`, using the absolute project root (forward slashes);
    - the `plugin` array entry — `"./cortex-toolkit"` when the toolkit is a submodule in the project, otherwise `"cortex-toolkit@git+https://github.com/etelyatn/cortex-toolkit.git"`. Append, never replace existing entries, and skip entries already present. Never write to the user's global `~/.config/opencode/opencode.json`.
 8. Offer context-block injection into `CLAUDE.md` and `AGENTS.md` using the toolkit templates, filtered to detected domains.
 9. Summarize the engine path, detected domains, created files, MCP settings, and recommended next actions.
 10. If the user works in Codex, run the **Codex Verification Gate** below before declaring setup complete. "Config written" and "Codex ready" are separate states.

If the plugin is missing, stop and tell the user to add the UnrealCortex submodule first.
If the plugin is explicitly disabled in the `.uproject`, stop until they enable it.

## Codex Verification Gate

Run whenever the user works in Codex and setup or config files changed. The project can be fully configured while the active Codex session still cannot see Cortex, so never equate "config written" with "Codex ready".

### Checklist (run in order)

1. **CLI + plugin present.** Confirm `codex` is installed and the toolkit plugin is enabled:
   ```bash
   codex --version
   codex plugin list | grep cortex-toolkit
   ```
   If the plugin is missing or disabled, run the install steps in `.codex/INSTALL.md`, then restart Codex and re-run this gate.
2. **Project root aligned.** The session must have been started from the project root (where `.uproject` and `.mcp.json` live). If it was started elsewhere, the project is not detected:
   - stop Codex, start a fresh session from the project root (`cd <project-root> && codex`), then re-run this gate.
3. **Config picked up / session reload.** If `.mcp.json`, `AGENTS.md`, or the toolkit plugin changed after the session started, the session is stale:
   - stop Codex and start a fresh session — that is the only reliable reload. Do not assume edits are hot-picked-up.
4. **Trusted project.** Codex prompts to trust a project before running hooks or loading context. An untrusted project silently disables them:
   - approve the trust prompt, or add the project root to the trusted projects list, then restart the session.
5. **Editor + MCP health.** Confirm the Unreal Editor is running and MCP is reachable:
   - call `get_status` (or `editor_cmd(get_editor_state)`). If it fails, use `cortex-editor`.
6. **MCP surfaced vs loaded.** A non-zero MCP server count does not guarantee the custom `cortex_mcp_*` tools are exposed to the active agent interface:
   - confirm `cortex_mcp` is in the runtime's MCP/server list and that a Cortex tool (e.g., `get_status`) is actually callable.
   - if the server is loaded but the tools are not surfaced, restart the session and re-check.

### Completion gate

Only report Codex as ready when all of the following hold: project root correct; `.mcp.json` present and valid; Unreal Editor running with a fresh port file; the session was restarted after the latest config change; and Cortex MCP is visible in the current runtime.

## Onboarding Mode

Guide a new or returning user through setup, editor connectivity, and useful next actions.

### Re-run Detection

Check for `.cortex/onboarded`.

- If missing: run the full walkthrough below.
- If present: ask whether they want the full walkthrough or a short reference card.

### Phase 1: Environment Check

1. Check `.cortex/config.yaml`. If missing, direct the user to Init Mode and stop.
2. Check for a `Saved/CortexPort-*.txt` port file. If missing, direct the user to `cortex-editor` and stop.
3. Call `get_status` to verify editor and MCP connectivity.
4. Compare registered domains against `UnrealCortex.uplugin` modules and report missing domains if any.

### Phase 2: Orientation

Print a short reference card with:
- `cortex-setup` for onboarding, initialization, schema refresh, and discovery
- `cortex-editor` for editor lifecycle and MCP diagnostics
- `cortex-build` for compile/build work
- Domain skills: `cortex-blueprint`, `cortex-data`, `cortex-material`, `cortex-umg`, `cortex-level`, `cortex-statetree`, `cortex-animation`, `cortex-reflect`
- Testing skills: `cortex-qa`, `cortex-test`

### Phase 3: What's Next?

1. Call `reflect_cache_status` first. If the cache is missing or stale, make rebuilding it the first suggestion.
2. Gather live project signals with:
   - `get_data_catalog`
   - Blueprint listing under `/Game`
   - Widget Blueprint listing under `/Game`
   - `list_actors` with `limit=1`
   - `list_materials` under `/Game`
   - `statetree_cmd(command="list_assets", params={"path_filter": "/Game"})`
   - `anim_cmd(command="list_assets", params={"path": "/Game", "limit": 20})`
3. Check `.cortex/domains/*.md` for template-only or nearly empty files.
4. Generate ordered suggestions backed by detected content. Keep the order foundational -> analytical -> creative.
5. Stop after presenting suggestions. Do not auto-run one.

After Phase 3 completes, create `.cortex/onboarded` with the current date.

## Discovery Mode

Use file reads first. Reserve MCP calls for cases where local inspection cannot answer the question.

### Advisor Mode

1. Check whether `.cortex/config.yaml` exists.
2. Check whether a `Saved/CortexPort-*.txt` file exists.
3. Check whether `.cortex/schema/` exists and how fresh it is.
4. Inspect `Content/` for Data, Blueprints, Materials, UI, StateTrees, and Maps.
5. Review recent conversation context for active domain hints.

Return up to three suggestions, prioritized in this order:
1. Broken infrastructure
2. Missing setup or stale project knowledge
3. Active work context
4. Asset-backed exploration

Always ground every suggestion in a detected signal and include a concrete skill to run next.

### Catalog Mode

If the user asks for the full catalog, print the approved public surface:
- `cortex-setup`
- `cortex-editor`
- `cortex-build`
- `cortex-blueprint`
- `cortex-bp-migrate`
- `cortex-data`
- `cortex-umg`
- `cortex-material`
- `cortex-level`
- `cortex-statetree`
- `cortex-animation`
- `cortex-reflect`
- `cortex-test`
- `cortex-qa`

### Domain Mode

If the user asks for help within a specific domain, report:
- the relevant skill or skills
- matching project content counts
- schema or domain-context availability
- one concrete next action

Use `umg` terminology for UI guidance and route all QA guidance through `cortex-qa`.

### Agent Catalog Mode

If the user asks about specialist agents, group them by domain and explain that skills launch them automatically when needed.

## Schema Refresh Mode

Generate LLM-readable project schema files in `.cortex/schema/`.

1. Verify the Unreal Editor is running and the MCP connection is healthy. If not, direct the user to `cortex-editor`.
2. Call `schema_generate` with `domain: "all"`.
3. Review the output under `.cortex/schema/` and flag or remove engine-only or marketplace noise if it leaked through.
4. Read `.cortex/schema/_catalog.md` to verify the generated files.
5. Report which files were generated and any errors.
