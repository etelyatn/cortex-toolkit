# Cortex Toolkit — Codex Setup

See `.codex/INSTALL.md` for installation instructions.

## Prerequisites

- Git for Windows
- UnrealCortex plugin installed in your project
- `.mcp.json` configured with `cortex_mcp` server before using live UnrealCortex MCP tools

## Install

```bash
codex plugin marketplace add etelyatn/cortex-toolkit
codex plugin add cortex-toolkit@cortex-toolkit
```

Restart Codex if it was already running.
When Codex prompts to review toolkit hooks, trust them if you want automatic editor connection checks and session context loading.

## How Skills Are Discovered

Codex discovers skills from the installed `cortex-toolkit` plugin manifest at `.codex-plugin/plugin.json`, which exposes the toolkit's root-level `skills/` directory.

The plugin does not bundle `.mcp.json`; keep MCP configuration in your Unreal project because it needs project-specific absolute paths.

Codex also discovers `hooks/hooks.json` from the plugin. The PreToolUse hook guards `cortex_mcp` tool calls by checking the Unreal Editor connection, and the SessionStart hook loads Cortex project context.

## Limitations

- **Hooks require trust in Codex** — Codex prompts before running new or changed toolkit hooks.
- **Operational skills need a local editor** — Skills like `/cortex-editor` and `/cortex-build` require a local Unreal Editor and are not functional in Codex cloud environments.
- **MCP only** — Interact with Unreal Engine via the `cortex_mcp` MCP server.

## Troubleshooting

- **Skills not found:** Verify the Codex plugin is installed and enabled, then restart Codex.
- **MCP not connecting:** Ensure `.mcp.json` is configured and the Unreal Editor is running.
- **Editor not found:** Run `get_status` via MCP to check connectivity.

### "Configured but not surfaced in the current session"

The most common false-positive state: the project is configured, but the active Codex session cannot use Cortex yet. Treat **config written** and **Codex ready** as separate states. Check in this order:

1. **Session started before config reload.** If `.mcp.json`, `AGENTS.md`, or the toolkit plugin changed after the session began, the session is stale. Fix: stop Codex and start a fresh session from the project root. This is the only reliable reload — edits are not hot-picked-up.
2. **Wrong working directory.** The session must start from the project root (where `.uproject` and `.mcp.json` live). Fix: restart with `cd <project-root> && codex`.
3. **Project not trusted.** Codex disables hooks and context loading for untrusted projects. Fix: approve the trust prompt or add the project root to the trusted projects list, then restart the session.
4. **Unreal Editor reachable but Codex cannot use Cortex.** Fix: call `get_status`; if it fails, use the `cortex-editor` skill to start/connect the editor, then re-check.
5. **MCP loaded but tools not surfaced.** A non-zero MCP server count does not guarantee the custom `cortex_mcp_*` tools are exposed to the active agent interface. Fix: confirm `cortex_mcp` is listed and a Cortex tool (e.g., `get_status`) is callable; if loaded but not surfaced, restart the session.

### Verification checklist

Run after any setup change:

- [ ] Project root is correct (session started from the `.uproject` directory)
- [ ] `.mcp.json` is present and valid JSON with the `cortex_mcp` server
- [ ] Unreal Editor is running and the port file is fresh (`Saved/CortexPort-*.txt`)
- [ ] Codex session was restarted after the latest config change
- [ ] `cortex_mcp` is visible in the current runtime and `get_status` returns a response
