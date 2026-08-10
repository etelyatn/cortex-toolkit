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
