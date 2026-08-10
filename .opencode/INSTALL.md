# Cortex Toolkit — OpenCode Installation

## Prerequisites
- OpenCode (https://opencode.ai) installed
- UnrealCortex plugin installed in your Unreal project
- Python 3.10+ with uv (for the MCP server)

## Installation
Run `cortex-init` in your project and select OpenCode when asked which assistants to configure.
This writes the `plugin` entry and the `cortex_mcp` MCP server into `opencode.json` and copies the
Cortex agents into `.opencode/agents/`.

### Manual installation
Add to your project's `opencode.json`:

```json
{
  "plugin": ["./cortex-toolkit"],
  "mcp": {
    "cortex_mcp": {
      "type": "local",
      "command": ["uv", "run", "--directory", "D:/Path/To/Your/Project/Plugins/UnrealCortex/MCP", "cortex-mcp"],
      "environment": { "CORTEX_PROJECT_DIR": "D:/Path/To/Your/Project" }
    }
  }
}
```

Replace `D:/Path/To/Your/Project` with your project's absolute root (forward slashes). Use the same
absolute path form as `.mcp.json` — the MCP server consumes `CORTEX_PROJECT_DIR` as-is.

Use `"plugin": ["cortex-toolkit@git+https://github.com/etelyatn/cortex-toolkit.git"]` if the toolkit is
not a submodule in your project.

## Windows install issues
Some Windows OpenCode builds fail to resolve git-backed plugin specs (Bun cannot find `git.exe`).
Fallback:

```powershell
npm install cortex-toolkit@git+https://github.com/etelyatn/cortex-toolkit.git --prefix "$HOME\.config\opencode"
```

Then use `"plugin": ["~/.config/opencode/node_modules/cortex-toolkit"]`.

## Verify Installation
1. Restart OpenCode. In a new session ask "What Cortex skills are available?" — the agent should list Cortex skills.
2. `use skill tool to list skills` — the `cortex-*` skills should appear.
3. With the Unreal Editor running, `cortex-status` should report connection health.

## Troubleshooting
- Plugin not loading: check `opencode run --print-logs "hello" 2>&1 | grep -i cortex`.
- Skills not found: verify the plugin entry in `opencode.json` and restart OpenCode.
- MCP not connecting: confirm `cortex_mcp` is in `opencode.json` and the Unreal Editor is running.
