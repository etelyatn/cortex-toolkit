---
name: cortex-editor
description: Use when the Unreal Editor needs to be started, checked, reconnected, or restarted
---

# Cortex Editor

Single public workflow for editor lifecycle and MCP connectivity.

## Intent Routing

- "open editor", "start editor" -> Start Mode
- "check status", "why isn't Cortex connected?", "diagnose MCP" -> Status Mode
- "restart editor", "restart after C++ changes", "editor is wedged" -> Restart Mode
- "build", "compile", "UBT error" -> stop and route to `cortex-build`

## Start Mode

Use this when the editor is down and needs to be launched cleanly.

1. Check for a running `UnrealEditor.exe` process and use the layered readiness check: a valid `Saved/CortexPort-*.txt` port file with a healthy MCP probe, **or** a live MCP health probe on the default bind range when the editor is running but the port file is missing.
2. If the editor is already healthy (port file + probe, or probe without port file), report the port and registered domains, then stop.
3. Read the effective `engine.path` from `.cortex/config.yaml` plus optional `.cortex/config.local.yaml`. Fall back to `UE_PATH` only if project config does not provide it.

```bash
ENGINE_PATH=$(python cortex-toolkit/lib/cortex_config.py --project-dir . --get engine.path)
```

4. If no project config exists, direct the user to `cortex-setup` first.
5. Verify the `.uproject` exists and that `UnrealCortex` is not explicitly disabled. If the `.uproject` explicitly sets `UnrealCortex` to `"Enabled": false`, stop and tell the user to enable it before launching.
6. If a UE process exists without a valid port file, tell the user the editor may still be starting or blocked by a modal dialog and ask whether to wait or relaunch.
7. Remove stale port files only after confirming there is no healthy editor instance.

```bash
for f in Saved/CortexPort-*.txt; do
  [ -f "$f" ] || continue
  PID=$(echo "$f" | sed 's/.*CortexPort-\([0-9]*\).*/\1/')
  if [ -n "$PID" ] && MSYS_NO_PATHCONV=1 tasklist /FI "PID eq $PID" /NH 2>/dev/null | grep -q "$PID"; then
    continue
  fi
  rm -f "$f"
done
rm -f Saved/CortexPort.txt 2>/dev/null || true
```

8. Launch the editor with:
   - `-AutoDeclinePackageRecovery`
   - `-ExecCmds="Mainframe.ShowRestoreAssetsPromptOnStartup 0"`

```bash
UPROJECT=$(ls *.uproject 2>/dev/null | head -1)
"$ENGINE_PATH/Engine/Binaries/Win64/UnrealEditor.exe" "$(pwd)/$UPROJECT" -AutoDeclinePackageRecovery -ExecCmds="Mainframe.ShowRestoreAssetsPromptOnStartup 0" &
```

9. Poll every 5 seconds for up to 120 seconds using the layered readiness check: process alive → port file present → live MCP health probe (`get_status`). A successful probe counts as ready even if the port file never appears. At 30 seconds, tell the user the editor may be compiling shaders. At 60 seconds, suggest checking the editor window for modal dialogs.
10. Once ready, read the port and verify MCP before calling MCP tools. If the port file is present, use it (preferred discovery); if MCP is healthy but the port file is missing, proceed anyway and say so explicitly:

```bash
RAW=$(cat Saved/CortexPort-*.txt 2>/dev/null | head -1 | tr -d '[:space:]')
if [[ "$RAW" =~ ^[0-9]+$ ]]; then
  PORT="$RAW"
elif [[ "$RAW" =~ \"port\":([0-9]+) ]]; then
  PORT="${BASH_REMATCH[1]}"
fi
if [ -n "$PORT" ]; then
  (echo > /dev/tcp/127.0.0.1/$PORT) 2>/dev/null && echo "TCP OK"
fi
```

11. Report success with the port and registered domains. If readiness came from the live MCP probe without a port file, report: editor running, MCP reachable, port file missing. On timeout, distinguish: editor never started vs. editor started but MCP never became reachable.

## Status Mode

Use this when the editor may already be running but MCP connectivity or domain registration is suspect.

1. Check whether `UnrealEditor.exe` is running.
2. Inspect `Saved/CortexPort-*.txt` and identify the active port file.
3. Call `get_status` to validate the full chain: assistant client -> MCP server -> TCP -> CortexCore.
4. Compare registered domains against the project's expected domains and report any missing ones.
5. Print a concise summary:

```text
Editor:  ✓ Running (PID 12345)
Port:    ✓ 8742
MCP:     ✓ Connected
Domains: ✓ data, blueprint, umg, material, level, qa, reflect, statetree
```

### Reconnect Protocol

Run this only if `get_status` fails while the editor still appears to be running.

1. Re-verify that the editor process is still alive.
2. Re-check the port file and wait briefly if the editor is still initializing.
3. Retry `get_status` up to 4 times over about 55 seconds, with increasing waits between attempts.
4. If the connection comes back, report the restored port, domains, and server version.
5. If it still fails, tell the user that manual reconnect or a full `cortex-editor` restart path is required and stop rather than retrying indefinitely.

## Restart Mode

Use this when the editor is wedged or must be restarted after code changes.

1. Check current state: editor process, port file, and whether the request is really just a start request.
2. Check for unsaved work with `core_cmd(command="list_dirty_packages")` (`count`, `packages: [{package, file}]`; `file` is empty for a never-saved package) and ask whether to save assets before restart.
3. If the user wants a build, stop and route them to `cortex-build`. Do not run build steps inside this skill.
4. Call `editor_restart` (`timeout` default 120, `force` default `false`). The restart is not unconditional: `force` is passed to `core.shutdown`, so with dirty packages and `force=false` it is refused with `UNSAVED_CHANGES` (the dirty packages are listed in `dirty_packages`), nothing is shut down and the editor keeps running. Ask the user to save those assets or to confirm discarding them, and only then repeat the call with `force: true`. Never pass `force: true` on your own.
5. The engine is taken from the running editor (its executable), falling back to the `.uproject` `EngineAssociation`. There is no `UE_56_PATH` and no manual engine selection; if neither resolves, the call fails with `INVALID_OPERATION` before anything is shut down.
6. Success means the old process exited, the relaunched process published its own port file and `get_status` reported the project. Report `port`, `old_pid` and `new_pid` (the result has no `pid`), `engine_path`, the registered `domains` and `restart_time_seconds`.

If restart fails, report the error and give the user the relevant manual recovery path. Read the failure fields: `relaunch_attempted: false` means nothing was launched (the engine or the old pid could not be resolved, or `core.shutdown` refused); `editor_running: true` means the relaunched editor (`editor_pid`) is still starting, so wait for its port file rather than launching another; `editor_running: false` means no relaunched editor is running (`exit_code` says why) and the user must launch it manually. `launch_attempts` is 1 unless the first launch exited before reporting a port.

## Editor Command Notes

Use these through `editor_cmd` when driving PIE or reading editor state:

- `start_pie` / `restart_pie` take `mode`: `selected_viewport` (default, plays inside the active level viewport) or `new_window` (floating PIE window). Any other value is `INVALID_FIELD` and changes no PIE state.
- `execute_console_command` runs in the PIE world while PIE is active, else in the editor world (`EDITOR_NOT_READY` only when neither exists). The response reports `world` (`pie`/`editor`) and `route` (`world_exec`, `console` or `engine_exec`; `stat` commands use `engine_exec`).
- `capture_screenshot` takes `source`: `auto` (default: the PIE window while PIE runs, else the level viewport), `editor` (scene only) or `pie` (`PIE_NOT_ACTIVE` without PIE). The PIE window capture includes UMG; the response reports `source` and `includes_ui`.
- `get_recent_logs` takes `contains`, a case-insensitive substring filter on the message, combinable with `category` and `severity`.
- `inject_mouse` moves are Slate pointer events only: gameplay code that reads the OS cursor through the scene viewport (`GetMousePosition`, deprojection) does not see them. For cursor-driven gameplay use a Cortex Replay recording (`cortex-replay` skill).
