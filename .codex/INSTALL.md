# Installing Cortex Toolkit for Codex

Enable Cortex Toolkit skills in Codex via native skill discovery.

## Prerequisites

- Git

## Installation

1. Clone the repository:

```bash
git clone https://github.com/etelyatn/cortex-toolkit.git ~/.codex/cortex-toolkit
```

2. Create the skills symlink:

```bash
mkdir -p ~/.agents/skills
ln -s ~/.codex/cortex-toolkit/skills ~/.agents/skills/cortex
```

Windows (PowerShell):

```powershell
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.agents\skills"
cmd /c mklink /J "$env:USERPROFILE\.agents\skills\cortex" "$env:USERPROFILE\.codex\cortex-toolkit\skills"
```

3. Restart Codex (quit and relaunch) so skills are discovered.

## Verify

Prompt Codex:

```text
Use cortex-help to show available Cortex Toolkit skills.
```

Then run project setup:

```text
Use cortex-init to configure this Unreal project and ensure .mcp.json contains cortex_mcp settings.
```

## Updating

```bash
cd ~/.codex/cortex-toolkit && git pull
```

Skills update instantly through the symlink/junction.

## Uninstalling

```bash
rm ~/.agents/skills/cortex
```

Windows (PowerShell):

```powershell
Remove-Item "$env:USERPROFILE\.agents\skills\cortex"
```

Optionally remove the clone:

```bash
rm -rf ~/.codex/cortex-toolkit
```
