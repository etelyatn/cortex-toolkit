---
name: cortex-status
description: Use when checking MCP connection health, editor status, diagnosing connectivity issues, or verifying domain registration
---

# Cortex Status

Diagnostic chain for MCP connectivity and domain health.

## Steps

### 1. Check Editor Process

Look for a running UnrealEditor process. On Windows:
```bash
tasklist | grep -i UnrealEditor
```

If not running → report "Editor not running" and suggest `/cortex-editor`.

### 2. Check Port File

List `Saved/CortexPort-*.txt`. CortexCore writes one file per editor instance named `CortexPort-{PID}.txt`.

Run from the project root (directory containing `*.uproject`):
```bash
ls Saved/CortexPort-*.txt 2>/dev/null || echo "No port files found"
```

If none found → editor may be starting up or CortexCore plugin is not loaded.
If multiple found → multiple editors are running; MCP will select the most recently started one.

### 3. Verify MCP Connection

Call the `get_status` MCP tool. This validates the full chain: Claude → MCP server → TCP → CortexCore.

Report the response: server version, connected domains, uptime.

### 4. Check Domain Registration

Call `get_status` and verify expected domains are registered based on `.cortex/config.yaml`.

Report any missing domains — the corresponding UE module may not be enabled in `.uplugin`.

### 5. Report Summary

Format as a diagnostic chain:
```
Editor:  ✓ Running (PID 12345)
Port:    ✓ 8742
MCP:     ✓ Connected
Domains: ✓ data, blueprint, graph, umg
```

If any step fails, stop and report the failure with remediation steps.
