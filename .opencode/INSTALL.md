# Cortex Toolkit — OpenCode Installation

## Prerequisites
- OpenCode (https://opencode.ai) installed
- UnrealCortex plugin installed in your Unreal project
- Python 3.10+ with uv (for the MCP server)

## Quick Start

1. **Install** — open your project in OpenCode and paste:

   ```
   Fetch and follow instructions from https://raw.githubusercontent.com/etelyatn/cortex-toolkit/main/.opencode/INSTALL.md
   ```

   The agent adds the toolkit plugin to `opencode.json`:
   `"plugin": ["cortex-toolkit@git+https://github.com/etelyatn/cortex-toolkit.git"]`.
2. **Restart OpenCode** — the toolkit installs from git and registers the `cortex-*` skills.
3. **Configure** — run `cortex-init` and choose OpenCode; it creates `.cortex/` and wires the `cortex_mcp` MCP server.
4. **Connect** — run `cortex-editor` to start the Unreal Editor, then `cortex-status` to verify the connection.
5. **Onboard** — run `cortex-start` for guided onboarding, then `cortex-schema-refresh` to index your project.
6. **Use** — ask `cortex-help` anytime; `cortex-*` domain skills work while the editor is running.

If the plugin fails to load, see [Windows install issues](#windows-install-issues).

## Installation

Add the toolkit to the `plugin` array in your project's `opencode.json` (or the global `~/.config/opencode/opencode.json`):

```json
{
  "plugin": ["cortex-toolkit@git+https://github.com/etelyatn/cortex-toolkit.git"]
}
```

Restart OpenCode. OpenCode fetches the toolkit from git through its plugin manager, loads
`.opencode/plugins/cortex.js`, and registers the `cortex-*` skills.

Verify by asking: "What Cortex skills are available?" — OpenCode should list Cortex skills.

## Project Setup

Run `cortex-init` in your project and select OpenCode when asked which assistants to configure.
This creates `.cortex/` and writes the `plugin` entry and the `cortex_mcp` MCP server into `opencode.json`.
If the toolkit is a vendored submodule, `cortex-init` writes:

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

Replace `D:/Path/To/Your/Project` with your project's absolute root (forward slashes). On macOS/Linux, paths start with `/` (e.g. `/home/user/MyProject`). Use the same
absolute path form as `.mcp.json` — the MCP server consumes `CORTEX_PROJECT_DIR` as-is.

`cortex-init` picks the `plugin` entry automatically: `./cortex-toolkit` when the toolkit is a submodule
in your project, otherwise `cortex-toolkit@git+https://github.com/etelyatn/cortex-toolkit.git`. Existing
entries are never duplicated. Note: `cortex-init` writes to the project-level `opencode.json` only; if you
installed the plugin in the global config, add the `cortex_mcp` MCP entry manually.

### Vendored submodule alternative

If your project already ships the toolkit as a submodule (like CortexSandbox), skip the git spec and use
`"plugin": ["./cortex-toolkit"]` — the toolkit lives in the repo.

## Windows install issues
Some Windows OpenCode builds fail to resolve git-backed plugin specs (Bun cannot find `git.exe`).
Fallback:

```powershell
npm install cortex-toolkit@git+https://github.com/etelyatn/cortex-toolkit.git --prefix "$HOME\.config\opencode"
```

Then use `"plugin": ["~/.config/opencode/node_modules/cortex-toolkit"]`.

## Verify Installation
1. Restart OpenCode. In a new session ask "What Cortex skills are available?" — OpenCode should list Cortex skills.
2. `use skill tool to list skills` — the `cortex-*` skills should appear.
3. With the Unreal Editor running, `cortex-status` should report connection health.

## Troubleshooting
- Plugin not loading: check `opencode run --print-logs "hello" 2>&1 | grep -i cortex`.
- Skills not found: verify the plugin entry in `opencode.json` and restart OpenCode.
- MCP not connecting: confirm `cortex_mcp` is in `opencode.json` and the Unreal Editor is running.
