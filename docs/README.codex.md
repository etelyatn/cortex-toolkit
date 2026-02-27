# Cortex Toolkit for Codex

Guide for using Cortex Toolkit with Codex via native skill discovery.

## Quick Install

Tell Codex:

```text
Fetch and follow instructions from https://raw.githubusercontent.com/etelyatn/cortex-toolkit/refs/heads/main/.codex/INSTALL.md
```

## Manual Installation

1. Clone the repo:

```bash
git clone https://github.com/etelyatn/cortex-toolkit.git ~/.codex/cortex-toolkit
```

2. Create the skills symlink:

```bash
mkdir -p ~/.agents/skills
ln -s ~/.codex/cortex-toolkit/skills ~/.agents/skills/cortex
```

Windows:

```powershell
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.agents\skills"
cmd /c mklink /J "$env:USERPROFILE\.agents\skills\cortex" "$env:USERPROFILE\.codex\cortex-toolkit\skills"
```

3. Restart Codex.

## How It Works

- Codex discovers skills from `~/.agents/skills/` at startup.
- Cortex Toolkit exposes a unified `skills/` folder for Codex.
- Skill names are the same as Claude for parity (`cortex-init`, `cortex-start`, `cortex-help`, and domain skills).
- In Codex, invoke skills by naming them in your request.

## MCP Configuration

Use `cortex-init` for project setup:

- Creates `.cortex/` project memory files if missing.
- Creates or patches `.mcp.json`.
- Upserts only `mcpServers.cortex_mcp`.
- Preserves unrelated MCP server definitions and top-level config keys.

Expected MCP entry:

```json
{
  "mcpServers": {
    "cortex_mcp": {
      "command": "uv",
      "args": ["run", "--directory", "Plugins/UnrealCortex/MCP", "cortex-mcp"],
      "env": {
        "CORTEX_PROJECT_DIR": "."
      }
    }
  }
}
```

## Updating

```bash
cd ~/.codex/cortex-toolkit && git pull
```

## Troubleshooting

1. Skills are not detected:
   - Verify link/junction exists: `~/.agents/skills/cortex`
   - Verify skill folders exist: `~/.codex/cortex-toolkit/skills`
   - Restart Codex
2. MCP tools fail:
   - Ensure Unreal Editor is open with UnrealCortex enabled
   - Ensure `.mcp.json` has `cortex_mcp` entry
   - Ensure `uv` is installed and available on PATH
