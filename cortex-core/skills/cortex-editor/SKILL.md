---
name: cortex-editor
description: Use when the Unreal Editor needs to be running, MCP connection fails, or user asks to start or open the editor
---

# Cortex Editor

Editor lifecycle management — detect, start, and verify the Unreal Editor.

## Steps

### 1. Check If Running

Check for UnrealEditor process and verify `Saved/CortexPort.txt` exists:
```bash
tasklist | grep -i UnrealEditor
```

If running and port file exists, read the port and verify TCP responds via `get_status` MCP tool. If healthy → report status and exit.

### 2. Read Configuration

Read engine path from `.cortex/config.yaml` under `engine.path`.

If no config → tell user to run `/cortex-init` first, or ask for the engine path directly.

Find the `.uproject` file in the project root.

### 3. Start Editor

Launch the editor in the background:
```bash
"$ENGINE_PATH/Engine/Binaries/Win64/UnrealEditor.exe" "<path to .uproject>" -AutoDeclinePackageRecovery &
```

> **Note:** `-AutoDeclinePackageRecovery` suppresses the "Restore Packages" modal that appears after a crash. Without it, the editor blocks waiting for user input and never reaches a usable state. We avoid `-unattended` because that suppresses all dialogs.

### 4. Wait for Ready

Poll for `Saved/CortexPort.txt` to appear (CortexCore writes it on startup). Check every 5 seconds, timeout after 120 seconds.

```bash
# Poll loop
for i in {1..24}; do
  if [ -f "Saved/CortexPort.txt" ]; then
    break
  fi
  sleep 5
done
```

### 5. Verify Connection

Once port file appears, read the port number and call `get_status` MCP tool to verify the full chain is healthy.

### 6. Report

Print: "Editor running on port {port}, MCP ready" with registered domains.

If timeout → report "Editor did not start within 120 seconds" and suggest checking UE logs in `Saved/Logs/`.
