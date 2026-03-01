# Cursor Setup Guide

## Prerequisites

- [Cursor](https://www.cursor.com/) editor
- [UnrealCortex](https://github.com/etelyatn/UnrealCortex) plugin installed in your UE project
- `.mcp.json` configured with `cortex_mcp` server

## Installation

Cursor discovers plugins via the `plugin.json` manifest at the root of a plugin directory.

1. Clone the repository:
   ```bash
   git clone https://github.com/etelyatn/cortex-toolkit.git
   ```

2. Point Cursor at the plugin directory (the repo root, which contains `.cursor-plugin/plugin.json`):
   - Open Cursor settings and navigate to the plugins or extensions section.
   - Add the path to the cloned repository.

3. Restart Cursor — skills, agents, and commands are loaded from the paths declared in `.cursor-plugin/plugin.json`.

## What Works

- **Skills** (`skills/`): All workflow skills are available for use in Cursor chat and Composer.
- **Agents** (`agents/`): Agent definitions (system prompts, resource references) load automatically.
- **Commands** (`commands/`): Operational commands that invoke shell tools (build, open editor, status checks) are supported where Cursor allows terminal access.

## What May Not Work

- **Hooks** (`hooks/hooks.json`): The `PreToolUse` hook that checks for a running Unreal Editor before each MCP call is defined in `hooks/hooks.json`. Whether Cursor executes hooks depends on the Cursor plugin API version. If hooks are not supported, verify editor connectivity manually by calling `get_status` before using MCP tools.

## Updating

```bash
cd /path/to/cortex-toolkit && git pull
```

Cursor picks up changes on the next restart.
