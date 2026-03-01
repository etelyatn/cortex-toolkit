# Codex Setup Guide

## Prerequisites

- Git
- [UnrealCortex](https://github.com/etelyatn/UnrealCortex) plugin installed in your UE project
- `.mcp.json` configured with `cortex_mcp` server

## Installation

See [`.codex/INSTALL.md`](../.codex/INSTALL.md) for step-by-step instructions.

The short version:

1. Clone the repository to `~/.codex/cortex-toolkit`
2. Symlink the `skills/` directory into `~/.agents/skills/cortex-toolkit`
3. Restart Codex — skills are auto-discovered via the symlink

## How Skills Are Discovered

Codex discovers skills by scanning `~/.agents/skills/`. The symlink created during installation points Codex to the `skills/` directory in this repository, so any skill file present there becomes available automatically. Updating the repo (via `git pull`) updates skills without any additional steps.

## Limitations

- **No hooks:** The `PreToolUse` editor connectivity check is Claude Code-only. In Codex, verify editor connectivity manually by calling `get_status` before using MCP tools.
- **No operational commands:** Commands such as `cortex-build`, `cortex-editor`, and `cortex-status` require a local shell and Unreal Editor — they are not available in Codex agents.
- **Subagent compatibility:** Many toolkit skills dispatch `cortex-toolkit:*` subagents. If your Codex build does not support these subagent types, run those workflows in Claude Code or Cursor.
- **Commands directory:** The `commands/` directory is not applicable to Codex.

## Updating

```bash
cd ~/.codex/cortex-toolkit && git pull
```
