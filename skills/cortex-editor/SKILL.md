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

1. Check for a running `UnrealEditor.exe` process and a live `Saved/CortexPort-*.txt` port file.
2. If the editor is already healthy, report the port and registered domains, then stop.
3. Read the effective `engine.path` from `.cortex/config.yaml` plus optional `.cortex/config.local.yaml`. Fall back to `UE_PATH` only if project config does not provide it.
4. If no project config exists, direct the user to `cortex-setup` first.
5. Verify the `.uproject` exists and that `UnrealCortex` is not explicitly disabled.
6. If a UE process exists without a valid port file, tell the user the editor may still be starting or blocked by a modal dialog and ask whether to wait or relaunch.
7. Remove stale port files only after confirming there is no healthy editor instance.
8. Launch the editor with:
   - `-AutoDeclinePackageRecovery`
   - `-ExecCmds="Mainframe.ShowRestoreAssetsPromptOnStartup 0"`
9. Poll for a new port file, then verify TCP first and `get_status` second.
10. Report success with the port and registered domains, or report startup diagnostics and the latest log tail on timeout.

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
2. Ask whether to save assets before restart.
3. If the user wants a build, stop and route them to `cortex-build`. Do not run build steps inside this skill.
4. Call `editor_restart` to perform the graceful shutdown, relaunch, port-file wait, and connection verification.
5. Report the new port, process ID, registered domains, and total restart time.

If restart fails, report the error and give the user the relevant manual recovery path.
