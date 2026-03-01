# Installing Cortex Toolkit for Codex

## Prerequisites

- Git
- [UnrealCortex](https://github.com/etelyatn/UnrealCortex) plugin installed in your UE project
- `.mcp.json` configured with `cortex_mcp` server

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/etelyatn/cortex-toolkit.git ~/.codex/cortex-toolkit
```

### 2. Create the skills symlink

**Unix/macOS:**
```bash
mkdir -p ~/.agents/skills
ln -s ~/.codex/cortex-toolkit/skills ~/.agents/skills/cortex-toolkit
```

**Windows (PowerShell as Admin):**
```powershell
New-Item -ItemType Directory -Path "$env:USERPROFILE\.agents\skills" -Force
New-Item -ItemType Junction -Path "$env:USERPROFILE\.agents\skills\cortex-toolkit" -Target "$env:USERPROFILE\.codex\cortex-toolkit\skills"
```

### 3. Restart Codex

Skills will be auto-discovered on restart.

## Verify Installation

```bash
ls -la ~/.agents/skills/cortex-toolkit
```

## Updating

```bash
cd ~/.codex/cortex-toolkit && git pull
```

Skills update automatically via the symlink.

## Notes

- Operational commands (`cortex-build`, `cortex-editor`, `cortex-status`, etc.) are not available in Codex — they require a local Unreal Editor.
- Hooks (PreToolUse editor check) are Claude Code-only. Codex agents should check editor connectivity manually.
