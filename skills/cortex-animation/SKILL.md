---
name: cortex-animation
description: Use when inspecting skeletal animation assets or authoring sequence skeleton named notifies through UnrealCortex.
---

# Cortex Animation

Work with Unreal skeletal animation assets through the `anim` MCP domain.

## Before Using Tools

1. Read `.cortex/domains/anim.md` if present.
2. Prefer `anim_cmd(command="...", params={...})` and use exact command names from live capabilities.
3. Inspect first and use the returned shared Cortex `fingerprint` as `expected_fingerprint` before any mutation.

## Supported Surface

Inspection:

- `list_assets`
- `get_sequence_info`
- `get_montage_info`
- `get_skeleton_info`
- `get_animbp_info`

Authoring is intentionally narrow and capability-gated:

- `add_named_notify`
- `update_named_notify`
- `remove_named_notify`
- `add_curve`
- `set_curve_keys`
- `remove_curve`
- `add_montage_section`
- `update_montage_section`
- `remove_montage_section`
- `add_socket`
- `set_socket_transform`
- `remove_socket`

Named notify mutations apply only to zero-duration sequence skeleton named notifies. Float curves apply to `UAnimSequence`, montage sections to `UAnimMontage`, and sockets to `USkeleton`. All mutations require `asset_path`, a precise input or selector, and `expected_fingerprint`; they support `dry_run` and optional `save` (`false` by default). Use a Phase B2 family only when live capabilities advertise that complete family.

## Guardrails

- Use `dry_run=true` before destructive or uncertain changes.
- Treat stale fingerprint errors as a signal to re-inspect and ask whether to retry.
- Do not call or invent object notify, notify state, AnimBP authoring, blendspace, retargeting, runtime preview, or animation `save_asset` commands.
- If a command is absent from live capabilities, report that the requested animation authoring is unavailable.

## Verification

For C++ domain changes, run:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "& { Set-Location 'cli/Testing'; .\RunTests.ps1 'Cortex.Animation+' }"
```

For MCP scenario coverage with an editor running:

```bash
cd Plugins/UnrealCortex/MCP && uv run pytest tests/test_mcp_scenarios.py -v -k animation
```
