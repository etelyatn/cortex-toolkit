# Cortex Toolkit — OpenCode Setup

See `.opencode/INSTALL.md` for installation instructions.

## Install
Run `cortex-init` and select OpenCode, or add the plugin + MCP entries to `opencode.json` manually.

## How Skills Are Discovered
The installed plugin's `config` hook registers the toolkit's `skills/` directory with OpenCode, so all
`cortex-*` skills appear in the native `skill` tool.

## How Agents Work
OpenCode discovers agents only from the project's `.opencode/agents/` directory. `cortex-init` copies
the generated agent wrappers there. Skills dispatch agents via the `task` tool using the agent name.

## Limitations
- No inline editor guard: if a `cortex_mcp_*` call fails with a connection error, load the
  `cortex-status` skill to diagnose and `cortex-editor` to start the editor.
- Operational skills need a local Unreal Editor.

## Troubleshooting
- Skills not found: verify the plugin entry and restart OpenCode.
- MCP not connecting: ensure `cortex_mcp` is configured and the editor is running.
