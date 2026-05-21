# Cortex Toolkit — Codex Setup

See `.codex/INSTALL.md` for installation instructions.

## Prerequisites

- Git
- UnrealCortex plugin installed in your project
- `.mcp.json` configured with `cortex_mcp` server before using live UnrealCortex MCP tools

## Install

```bash
codex plugin marketplace add etelyatn/cortex-toolkit
codex plugin add cortex-toolkit@cortex-toolkit
```

Restart Codex if it was already running.

## How Skills Are Discovered

Codex discovers skills from the installed `cortex-toolkit` plugin manifest at `.codex-plugin/plugin.json`, which exposes the toolkit's root-level `skills/` directory.

The plugin does not bundle `.mcp.json`; keep MCP configuration in your Unreal project because it needs project-specific absolute paths.

## Limitations

- **Hooks are not packaged for Codex** — the `hooks/` directory remains for Claude Code and Cursor workflows.
- **Operational skills need a local editor** — Skills like `/cortex-editor`, `/cortex-restart`, and `/cortex-build` require a local Unreal Editor and are not functional in Codex cloud environments.
- **MCP only** — Interact with Unreal Engine via the `cortex_mcp` MCP server.

## Troubleshooting

- **Skills not found:** Verify the Codex plugin is installed and enabled, then restart Codex.
- **MCP not connecting:** Ensure `.mcp.json` is configured and the Unreal Editor is running.
- **Editor not found:** Run `get_status` via MCP to check connectivity.
