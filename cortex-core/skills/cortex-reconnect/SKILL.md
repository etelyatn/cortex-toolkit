---
name: cortex-reconnect
description: Use when MCP connection is lost or unresponsive. Attempts to reconnect to the Cortex MCP server automatically.
---

# Cortex Reconnect

Reconnect to the Cortex MCP server when connection is lost or unresponsive.

## When to Use

> **Note:** Most reconnection scenarios are now handled automatically. The PreToolUse hook verifies editor connectivity before every MCP call, and the TCP client re-reads `CortexPort.txt` on reconnect to pick up port changes. Use this skill only when automatic recovery has failed.

- MCP tools are failing with connection errors **after** the PreToolUse hook passed
- When `/cortex-status` reports MCP unavailable but editor is running
- Persistent connection issues that survive automatic retry

## Steps

### 1. Verify Editor is Running

Check if UnrealEditor process is running:
```bash
tasklist | grep -i UnrealEditor
```

**If NOT running:**
- MCP server cannot run without editor
- Inform user to start editor first using `/cortex-editor`
- Exit (cannot reconnect to non-existent server)

**If running:** Proceed to reconnection attempts.

### 2. Check Port File

Verify `Saved/CortexPort.txt` exists (written by CortexCore on startup):
```bash
cat Saved/CortexPort.txt
```

**If missing:**
- Editor is running but CortexCore plugin may not be loaded
- Wait 5 seconds and check again (editor may still be initializing)
- If still missing after 10 seconds, inform user that CortexCore plugin may not be enabled

**If exists:** Note the port number and proceed.

### 3. Attempt Reconnection

**IMPORTANT:** The MCP client in Claude Code may auto-reconnect when you attempt to use MCP tools. Try calling the `get_status` tool to trigger reconnection.

**Reconnection strategy (retry 4 times with delays):**

**Attempt 1:**
- Call `get_status` MCP tool
- If succeeds → connection restored, go to Step 4
- If fails → wait 10 seconds, continue to Attempt 2

**Attempt 2:**
- Call `get_status` MCP tool
- If succeeds → connection restored, go to Step 4
- If fails → wait 15 seconds, continue to Attempt 3

**Attempt 3:**
- Call `get_status` MCP tool
- If succeeds → connection restored, go to Step 4
- If fails → wait 15 seconds, continue to Attempt 4

**Attempt 4 (final):**
- Call `get_status` MCP tool
- If succeeds → connection restored, go to Step 4
- If fails → go to Step 5 (manual reconnection required)

**Total retry time: ~55 seconds**

### 4. Connection Restored

If `get_status` succeeds at any point:

Report success with details:
```
✓ MCP connection restored
  Port:    {port}
  Domains: {list of registered domains}
  Server:  {version}
```

Exit successfully.

### 5. Manual Reconnection Required

If all automatic attempts fail:

Inform the user:
```
✗ MCP automatic reconnection failed after 4 attempts.

The MCP server appears to be running (editor is active, port file exists),
but the Claude Code client cannot connect.

Please type `/mcp` in the terminal to force a manual reconnection, then retry your operation.

Troubleshooting:
- Check for firewall blocking localhost:{port}
- Verify no other process is using port {port}
- Check UE logs: Saved/Logs/CortexSandbox.log
- Restart editor if issue persists: use /cortex-editor
```

**Do NOT retry indefinitely.** Stop after ~1 minute and request user intervention.

## Important Notes

- **MCP server runs inside Unreal Editor** - it cannot be restarted independently
- **`/mcp` command** is a Claude Code CLI command that forces client reconnection
- **This skill attempts auto-reconnect** by calling MCP tools (may trigger client reconnect)
- **If auto-reconnect fails**, user must manually run `/mcp` command
- **Never wait longer than 60 seconds** - always timeout and ask for user help

## Success Criteria

- `get_status` MCP tool returns successful response
- Registered domains are listed
- Port number matches `Saved/CortexPort.txt`
