---
name: cortex-restart
description: Use when the Unreal Editor needs to be restarted, after C++ changes need recompilation, or when the editor is in a bad state and needs a clean restart
---

# Cortex Restart

Restart the Unreal Editor - optionally build first, then graceful shutdown, relaunch, and verify MCP connection.

Use skill names directly in instructions (for example `cortex-editor`).
**For Claude:** slash aliases are available (for example `/cortex-editor`).

> **Note:** For just starting the editor (not restarting), use `cortex-editor` instead. The PreToolUse hook auto-starts the editor before MCP calls; this skill is for explicit restart workflows.

## Steps

### 1. Check Current State

Check if editor is running:
```bash
tasklist | grep -i UnrealEditor
```

Check port file:
```bash
cat Saved/CortexPort-*.txt
```

If not running, ask user if they just want to start (redirect to `cortex-editor`).

### 2. Save Before Restart (Optional)

Ask the user: "Save all assets before restart?"

If yes, call `save_all` MCP tool (via `core.save_asset` with `path: "/Game/"` or similar).

### 3. Build (Optional)

Ask the user: "Build C++ before restart?"

If yes, run the project's documented UnrealBuildTool command (substitute your project name/uproject as needed):
```bash
# Replace CortexSandboxEditor / CortexSandbox.uproject with your project
"$UE_56_PATH/Engine/Binaries/DotNET/UnrealBuildTool/UnrealBuildTool.exe" CortexSandboxEditor Win64 Development -Project="$(pwd)/CortexSandbox.uproject" -WaitMutex -FromMsBuild
```

Wait for build completion. If build fails, report error and do not restart.

### 4. Restart

Call the `editor_restart` MCP tool. It handles:
- Graceful shutdown via `core.shutdown`
- Wait for process exit
- Launch new editor instance
- Wait for port file and verify MCP connection

Default timeout: 120 seconds.

### 5. Report

On success, report:
- New port number
- Process ID
- Registered domains
- Total restart time

On failure, report the error and suggest manual intervention.
