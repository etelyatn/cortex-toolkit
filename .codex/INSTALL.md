# Cortex Toolkit — Codex Installation

## Prerequisites

1. **Git** — required to clone the toolkit
2. **UnrealCortex plugin** — must be installed in your Unreal Engine project
3. **MCP configuration** — your project must have `.mcp.json` pointing to the `cortex_mcp` server

## Installation

### Windows (PowerShell as Administrator)

```powershell
# 1. Clone the toolkit
git clone https://github.com/etelyatn/cortex-toolkit.git ~/.cortex-toolkit

# 2. Create a symlink in your project root
New-Item -ItemType SymbolicLink -Path "skills" -Target "$HOME\.cortex-toolkit\skills"
```

### macOS/Linux

```bash
# 1. Clone the toolkit
git clone https://github.com/etelyatn/cortex-toolkit.git ~/.cortex-toolkit

# 2. Create a symlink in your project root
ln -s ~/.cortex-toolkit/skills skills
```

## Verify Installation

After installation, Codex should discover skills from the `skills/` symlink in your project root.

## Limitations

- **No hooks support** — Codex does not execute shell hooks. The `hooks/` directory is not used.
- **No operational skills** — Skills like `/cortex-editor`, `/cortex-restart`, and `/cortex-build` require a local Unreal Editor and are not functional in Codex cloud environments.
- **MCP tools only** — Use the `cortex_mcp` server tools directly (configured in `.mcp.json`).

## Project Memory

Before starting work, read:
- `.cortex/config.yaml` — engine path and active domains
- `.cortex/context.md` — project-specific conventions
- `.cortex/domains/*.md` — domain-specific knowledge
