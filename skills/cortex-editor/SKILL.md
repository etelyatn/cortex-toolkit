---
name: cortex-editor
description: Use when the Unreal Editor needs to be running, MCP connection fails, or user asks to start or open the editor
---

# Cortex Editor

Editor lifecycle management — detect, start, and verify the Unreal Editor.

> **Note:** The PreToolUse hook (`check-ue-editor.sh`) now auto-starts the editor when any MCP tool is called and the editor is down. This skill is for **explicit** editor management — when the user asks to start/restart the editor, when you need to verify status interactively, or when the hook's auto-start failed and the user chose to start manually.

## Steps

### 1. Check If Running

Check for UnrealEditor process and verify a `Saved/CortexPort-*.txt` port file exists:
```bash
tasklist | grep -i UnrealEditor
```

If running and port file exists, read the port and verify TCP responds via `get_status` MCP tool. If healthy → report status and exit.

### 2. Read Configuration

Read engine path from `.cortex/config.yaml` under `engine.path`.

If no config → tell user to run `cortex-init` first, or ask for the engine path directly.

Find the `.uproject` file in the project root.

#### 2b. Verify Plugin Is Enabled

After finding the `.uproject` file, parse its `Plugins` array:

```bash
UPROJECT=$(ls *.uproject 2>/dev/null | head -1)
PLUGIN_STATUS=$(python3 -c "
import json
with open('$UPROJECT', encoding='utf-8') as f:
    data = json.load(f)
plugins = data.get('Plugins', [])
match = [p for p in plugins if p.get('Name') == 'UnrealCortex']
if not match:
    print('missing')
elif not match[0].get('Enabled', False):
    print('disabled')
else:
    print('enabled')
" 2>/dev/null || echo "parse_error")
```

If `missing` or `disabled`: Print this message and STOP. Do not launch the editor.
```
UnrealCortex is not enabled in {UPROJECT}.

Enable it first:
1. Open the editor manually
2. Go to Edit -> Plugins -> search "UnrealCortex" -> Enable
3. Accept the beta warning, then restart the editor
4. Re-run cortex-editor

Alternatively, edit {UPROJECT}:
- If a "Plugins" array exists, add: { "Name": "UnrealCortex", "Enabled": true }
- If no "Plugins" key exists, add: "Plugins": [{ "Name": "UnrealCortex", "Enabled": true }]

Without the plugin enabled, the editor will start but CortexCore won't initialize and no port file will be written.
```

If `parse_error`: Warn and continue.
If `enabled`: Continue to Step 2c.

#### 2c. Check for Running Editor Process

Before launching a new editor, check if one is already running:

```bash
tasklist /FI "IMAGENAME eq UnrealEditor.exe" /FO CSV 2>/dev/null | grep -i UnrealEditor
```

If an UnrealEditor process exists but no port file was found in Step 1:
- Tell the user an editor process is running but no port file was found.
- Explain this usually means the editor is still starting, or UnrealCortex is not enabled.
- Ask whether to wait and poll for the port file, or proceed with a new launch.

### 3. Start Editor

Before launching, clean up stale port files from previous sessions (only after Step 1 confirmed no healthy running editor):

```bash
for f in Saved/CortexPort-*.txt; do
  [ -f "$f" ] || continue
  PID=$(echo "$f" | grep -oP 'CortexPort-\K[0-9]+')
  if [ -n "$PID" ] && kill -0 "$PID" 2>/dev/null; then
    continue
  fi
  rm -f "$f"
done
rm -f Saved/CortexPort.txt 2>/dev/null || true
```

This prevents stale dead-editor port files from short-circuiting readiness checks.

Launch the editor in the background:
```bash
"$ENGINE_PATH/Engine/Binaries/Win64/UnrealEditor.exe" "<path to .uproject>" -AutoDeclinePackageRecovery -ExecCmds="Mainframe.ShowRestoreAssetsPromptOnStartup 0" &
```

> **Note:** `-AutoDeclinePackageRecovery` suppresses the "Restore Packages" modal (crash recovery). `-ExecCmds="Mainframe.ShowRestoreAssetsPromptOnStartup 0"` suppresses the "Restore Open Assets" toast (reopens previously-open asset editors). Both ensure the editor starts clean without prompts. We avoid `-unattended` because that suppresses all dialogs.

### 4. Wait for Ready

Poll for a new `Saved/CortexPort-*.txt` file to appear. Provide graduated feedback.

Important: Do NOT call MCP tools during this poll phase. Verify TCP with bash only. Call MCP tools only after port file exists and TCP responds.

At 0s: print "Starting editor... (this typically takes 30-90 seconds)".

Poll every 5 seconds:

```bash
for i in {1..24}; do
  if ls Saved/CortexPort-*.txt 1>/dev/null 2>&1; then
    break
  fi
  if [ "$i" -eq 6 ]; then
    echo "Still starting... If this is the first launch, the editor may be compiling shaders."
  fi
  if [ "$i" -eq 12 ]; then
    echo "Still waiting - check the editor window for modal dialogs (beta warning, restore assets prompt)."
  fi
  sleep 5
done
```

On timeout (120s, no port file): print diagnostics and tail latest log:

```bash
LATEST_LOG=$(ls -t Saved/Logs/*.log 2>/dev/null | head -1)
echo "Editor started but CortexCore did not write a port file within 120 seconds."
echo "Possible causes:"
echo "1. UnrealCortex plugin not enabled"
echo "2. Plugin failed to load"
echo "3. A modal dialog is blocking startup"
echo "4. Editor crashed during startup"
if [ -n "$LATEST_LOG" ]; then
  echo "Last 10 log lines from $LATEST_LOG:"
  tail -10 "$LATEST_LOG"
fi
```

### 5. Verify Connection

Once port file appears, read the port and verify TCP with bash first:

```bash
PORT=$(cat Saved/CortexPort-*.txt 2>/dev/null | head -1 | tr -d '[:space:]')
(echo > /dev/tcp/127.0.0.1/$PORT) 2>/dev/null && echo "TCP OK"
```

Only after TCP is healthy, call `get_status` MCP tool to verify full MCP health.

### 6. Report

Print: "Editor running on port {port}, MCP ready" with registered domains.

If timeout → report "Editor did not start within 120 seconds" and suggest checking UE logs in `Saved/Logs/`.

> **Need a full restart?** Use `cortex-restart` instead — it handles graceful shutdown, optional C++ rebuild, relaunch, and MCP verification in one workflow.
