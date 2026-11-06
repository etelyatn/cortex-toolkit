# Cortex Toolkit — OpenCode Setup

See `.opencode/INSTALL.md` for installation instructions.

## Install
Tell OpenCode: "Fetch and follow instructions from https://raw.githubusercontent.com/etelyatn/cortex-toolkit/main/.opencode/INSTALL.md"

This installs the toolkit as an OpenCode plugin from git. Then run `cortex-setup` and select OpenCode to configure the project.

## How Skills Are Discovered
The installed plugin's `config` hook registers the toolkit's `skills/` directory with OpenCode, so all
`cortex-*` skills appear in the native `skill` tool.

The plugin registers skills unconditionally, but injects session context only when
`hooks.session_context: true` is set in `.cortex/config.yaml`. The PreToolUse editor guard is not
part of the OpenCode plugin; OpenCode ignores `hooks.editor_guard`.

## Limitations
- No inline editor guard: if a `cortex_mcp_*` call fails with a connection error, load the
  `cortex-setup` skill to diagnose and `cortex-editor` to start the editor.
- Operational skills need a local Unreal Editor.

## Troubleshooting
- Skills not found: verify the plugin entry and restart OpenCode.
- MCP not connecting: ensure `cortex_mcp` is configured and the editor is running.
