# Cortex Toolkit — Codex Installation

## Prerequisites

1. **Git for Windows** — required to clone the toolkit and run packaged hook scripts on Windows
2. **UnrealCortex plugin** — must be installed in your Unreal Engine project
3. **MCP configuration for live tools** — your project must have `.mcp.json` pointing to the `cortex_mcp` server before using UnrealCortex MCP tools

## Installation

```bash
codex plugin marketplace add etelyatn/cortex-toolkit
codex plugin add cortex-toolkit@cortex-toolkit
```

Restart Codex if it was already running.

## Verify Installation

After installation, Codex should discover Cortex Toolkit skills from the installed plugin.

Your Unreal project still needs a project-local `.mcp.json` because the UnrealCortex MCP server path depends on where the plugin is installed in that project:

Replace the UnrealCortex path with your actual plugin location, for example `Plugins/UnrealCortex/MCP` or `Plugins/Developer/UnrealCortex/MCP`.

```json
{
  "mcpServers": {
    "cortex_mcp": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "D:/UnrealProjects/YourProject/Plugins/Developer/UnrealCortex/MCP",
        "cortex-mcp"
      ],
      "env": {
        "CORTEX_PROJECT_DIR": "D:/UnrealProjects/YourProject"
      }
    }
  }
}
```

Open the Unreal Editor before using live MCP tools. CortexCore writes the port file during editor startup, and the MCP server discovers it automatically.

Codex discovers `hooks/hooks.json` automatically after install. On first use, review and trust the hooks when prompted. The PreToolUse hook checks the Unreal Editor connection before `cortex_mcp` calls, and the SessionStart hook loads Cortex project context.

## Limitations

- **Hooks require trust in Codex** — the `hooks/` directory is packaged and Codex prompts before running new or changed hooks.
- **Operational skills need a local editor** — Skills like `/cortex-editor` and `/cortex-build` require a local Unreal Editor and are not functional in Codex cloud environments.
- **MCP tools only** — Use the `cortex_mcp` server tools directly (configured in `.mcp.json`).

## Project Memory

Before starting work, read:
- `.cortex/config.yaml` — engine path and active domains
- `.cortex/context.md` — project-specific conventions
- `.cortex/domains/*.md` — domain-specific knowledge
