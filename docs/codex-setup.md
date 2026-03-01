# Cortex Toolkit — Codex Setup

See `.codex/INSTALL.md` for installation instructions.

## Prerequisites

- Git
- UnrealCortex plugin installed in your project
- `.mcp.json` configured with `cortex_mcp` server

## How Skills Are Discovered

Codex discovers skills via a `skills/` symlink in your project root pointing to `~/.cortex-toolkit/skills`. Create this symlink during installation (see `.codex/INSTALL.md`).

## Limitations

- **No hooks** — Codex does not run shell hooks on session start or tool events.
- **No operational skills** — Skills like `/cortex-editor`, `/cortex-restart`, and `/cortex-build` require a local Unreal Editor and are not functional in Codex cloud environments.
- **MCP only** — Interact with Unreal Engine via the `cortex_mcp` MCP server.

## Troubleshooting

- **Skills not found:** Verify the `skills/` symlink exists and points to the correct directory.
- **MCP not connecting:** Ensure `.mcp.json` is configured and the Unreal Editor is running.
- **Editor not found:** Run `get_status` via MCP to check connectivity.
