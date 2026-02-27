# Unified Skills Directory

This directory is the Codex discovery surface for Cortex Toolkit.

- Source skills live under each domain plugin (for example `cortex-core/skills/`).
- This directory is generated from domain sources by:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/sync-unified-skills.ps1
```

Run the sync script after adding or changing any domain skill.
