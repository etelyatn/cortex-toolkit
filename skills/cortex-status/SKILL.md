---
name: cortex-status
description: Use when checking MCP connection health, editor status, diagnosing connectivity issues, verifying domain registration, or recovering a lost MCP connection
---

# Cortex Status

Diagnostic chain for MCP connectivity and domain health. Includes automatic reconnection retry if diagnostics fail.

Use skill names directly in instructions (for example `cortex-editor`).
**For Claude:** slash aliases are available (for example `/cortex-editor`).

## Steps

### 1. Check Editor Process

Look for a running UnrealEditor process. On Windows:
```bash
tasklist | grep -i UnrealEditor
```

If not running → report "Editor not running" and suggest `cortex-editor`.

### 2. Check Port File

List `Saved/CortexPort-*.txt`. CortexCore writes one file per editor instance named `CortexPort-{PID}.txt`.

Run from the project root (directory containing `*.uproject`):
```bash
ls Saved/CortexPort-*.txt 2>/dev/null || echo "No port files found"
```

If none found → editor may be starting up or CortexCore plugin is not loaded.
If multiple found → multiple editors are running; MCP will select the most recently started one.

### 3. Verify MCP Connection

Call the `get_status` MCP tool. This validates the full chain: assistant client → MCP server → TCP → CortexCore.

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

If any step fails, stop and report the failure. If `get_status` fails, proceed to the **Reconnect Protocol** below before giving up.

---

## Reconnect Protocol

Activate ONLY if Step 3 (`get_status`) fails. The PreToolUse hook normally handles transient drops automatically — use this protocol only when automatic recovery has failed.

### R1. Verify Editor Is Still Running

```bash
tasklist | grep -i UnrealEditor
```

If NOT running → MCP server cannot run without editor. Inform user to start editor with `cortex-editor`. Exit.

If running → proceed.

### R2. Confirm Port File

```bash
cat Saved/CortexPort-*.txt
```

If missing → wait 5 seconds and check again (editor may still be initializing). If still missing after 10 seconds, inform user that CortexCore plugin may not be enabled.

If exists → note the port number and proceed to retry loop.

### R3. Retry Loop (4 attempts, ~55 seconds total)

**Attempt 1:** Call `get_status` → if succeeds go to R4. If fails → wait 10 seconds.

**Attempt 2:** Call `get_status` → if succeeds go to R4. If fails → wait 15 seconds.

**Attempt 3:** Call `get_status` → if succeeds go to R4. If fails → wait 15 seconds.

**Attempt 4 (final):** Call `get_status` → if succeeds go to R4. If fails → go to R5.

### R4. Connection Restored

Report:
```
✓ MCP connection restored
  Port:    {port}
  Domains: {list of registered domains}
  Server:  {version}
```

Return to Step 5 summary above.

### R5. Manual Reconnection Required

All automatic attempts failed. Inform the user:
```
✗ MCP automatic reconnection failed after 4 attempts.

The MCP server appears to be running (editor is active, port file exists),
but the MCP client cannot connect.

For clients with a manual reconnect command, run it, then retry your operation.
For Claude: run /mcp to force a manual reconnect.

Troubleshooting:
- Check for firewall blocking localhost:{port}
- Verify no other process is using port {port}
- Check UE logs: Saved/Logs/CortexSandbox.log
- Restart editor if issue persists: use cortex-editor
```

**Do NOT retry indefinitely.** Stop after ~1 minute and request user intervention.
