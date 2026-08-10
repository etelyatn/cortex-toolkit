#!/usr/bin/env bash
# PreToolUse guard: ensure Unreal Editor + CortexCore TCP are ready
# before any cortex_mcp tool call.
#
# Fast path (~50ms): port file valid + TCP responds → exit 0 silently
# Start path: lock-protected editor launch, 180s two-phase poll
# Fail path: exit 2 with Claude-directive stderr

set -uo pipefail

# Walk up from a starting directory looking for *.uproject
_walk_up_for_uproject() {
    local dir="$1" parent
    for _ in $(seq 1 20); do
        if ls "$dir"/*.uproject 2>/dev/null | head -1 | grep -q .; then
            echo "$dir"; return 0
        fi
        parent=$(dirname "$dir")
        [ "$parent" = "$dir" ] && break
        dir="$parent"
    done
    return 1
}

# Resolve project root: CLAUDE_PROJECT_DIR → walk-up from CWD → walk-up from script location
# The third fallback handles subagents whose CWD differs from the project root.
_find_project_dir() {
    if [ -n "${CLAUDE_PROJECT_DIR:-}" ] && [ -d "$CLAUDE_PROJECT_DIR" ]; then
        echo "$CLAUDE_PROJECT_DIR"; return 0
    fi
    _walk_up_for_uproject "$(pwd)" && return 0
    local script_dir
    script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" 2>/dev/null && pwd) || return 1
    _walk_up_for_uproject "$script_dir"
}

if [ -n "${CORTEX_CONFIG_TEST_MODE:-}" ] && [ -n "${PROJECT_DIR:-}" ]; then
    PROJECT_DIR="$PROJECT_DIR"
else
    PROJECT_DIR=$(_find_project_dir) || {
    cat >&2 <<'EOF'
Could not find the Unreal project root directory.
Tell the user: the PreToolUse hook could not locate a .uproject file.
Checked CLAUDE_PROJECT_DIR, walked up from CWD, and walked up from script location.
Ask them to set CLAUDE_PROJECT_DIR or ensure the cortex-toolkit is inside the project tree.
Do not proceed with MCP tool calls until the user resolves this.
EOF
        exit 2
    }
fi
LOCK_DIR="$PROJECT_DIR/Saved/cortex-ue-editor-starting.lock"
RESTART_LOCK="$PROJECT_DIR/Saved/CortexRestarting.lock"
TOOLKIT_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." 2>/dev/null && pwd)
CORTEX_CONFIG_LOADER="$TOOLKIT_ROOT/lib/cortex_config.py"

_python_bin() {
    if command -v python >/dev/null 2>&1; then
        echo "python"; return 0
    fi
    if command -v python3 >/dev/null 2>&1; then
        echo "python3"; return 0
    fi
    return 1
}

_read_effective_config_value() {
    local key="$1"
    local py
    py=$(_python_bin) || {
        echo "python or python3 is required to read Cortex config" >&2
        return 2
    }
    if [ ! -f "$CORTEX_CONFIG_LOADER" ]; then
        echo "Cortex config loader not found: $CORTEX_CONFIG_LOADER" >&2
        return 2
    fi
    "$py" "$CORTEX_CONFIG_LOADER" --project-dir "$PROJECT_DIR" --get "$key"
}

resolve_engine_path() {
    local engine_path config_error_file config_error status
    engine_path=""
    if [ -f "$PROJECT_DIR/.cortex/config.yaml" ]; then
        config_error_file=$(mktemp)
        if engine_path=$(_read_effective_config_value "engine.path" 2>"$config_error_file"); then
            engine_path=$(printf '%s' "$engine_path" | tr -d '\r')
        else
            status=$?
            config_error=$(cat "$config_error_file" 2>/dev/null)
            rm -f "$config_error_file"
            if [ -n "$config_error" ] || [ "$status" -ne 1 ]; then
                echo "Failed to read Cortex config: $config_error" >&2
                return 2
            fi
            engine_path=""
        fi
        rm -f "$config_error_file"
    fi
    if [ -z "$engine_path" ]; then
        engine_path="${UE_PATH:-}"
    fi
    printf '%s\n' "$engine_path"
}

if [ "${CORTEX_CONFIG_TEST_MODE:-}" = "resolve_engine_path" ]; then
    resolve_engine_path
    exit $?
fi

# Find the best available port file.
# Priority: CORTEX_EDITOR_PID pin → any per-PID file (most recent) → legacy CortexPort.txt
_find_port_file() {
    local saved="$PROJECT_DIR/Saved"
    if [ -n "${CORTEX_EDITOR_PID:-}" ] && [ -f "$saved/CortexPort-${CORTEX_EDITOR_PID}.txt" ]; then
        echo "$saved/CortexPort-${CORTEX_EDITOR_PID}.txt"; return 0
    fi
    local pid_file
    pid_file=$(ls -t "$saved"/CortexPort-*.txt 2>/dev/null | head -1)
    if [ -n "$pid_file" ]; then
        echo "$pid_file"; return 0
    fi
    [ -f "$saved/CortexPort.txt" ] && echo "$saved/CortexPort.txt" && return 0
    return 1
}

# ── Restart lock guard ────────────────────────────────────────────────────
# If another process is restarting the editor, wait instead of launching a duplicate.
if [ -f "$RESTART_LOCK" ]; then
    LOCK_TS=$(tr -d '[:space:]' < "$RESTART_LOCK" 2>/dev/null)
    if [[ "$LOCK_TS" =~ ^[0-9]+$ ]]; then
        LOCK_AGE=$(( $(date +%s) - LOCK_TS ))
    else
        LOCK_AGE=999
    fi

    if [ "$LOCK_AGE" -gt 300 ]; then
        rm -f "$RESTART_LOCK"
    else
        WAIT=0
        while [ $WAIT -lt 180 ] && [ -f "$RESTART_LOCK" ]; do
            sleep 3; WAIT=$((WAIT + 3))
        done
        if [ -f "$RESTART_LOCK" ]; then
            cat >&2 <<'EOF'
Editor restart timed out. Lock file still present.
Tell the user: an editor restart did not complete within 180s. Ask them to choose:
1. Delete Saved/CortexRestarting.lock and retry
2. Start the editor manually, then retry
3. Abort the current task
Do not proceed with MCP tool calls until the user chooses.
EOF
            exit 2
        fi
    fi
fi

# Probe a port for a real MCP health response (get_status). Stronger than a bare
# TCP connect: it proves the plugin's command loop is alive on the Game Thread.
_mcp_health_probe() {
    local port="$1" line
    exec 3<>/dev/tcp/127.0.0.1/"$port" 2>/dev/null || return 1
    printf '{"command":"get_status"}\n' >&3 2>/dev/null
    IFS= read -r -t 3 line <&3 2>/dev/null
    exec 3<&- 3>&- 2>/dev/null
    [[ "$line" == *'"success":true'* ]]
}

# Parse the port from a port file (supports plain-number and JSON formats).
_read_port_from_file() {
    local port_file="$1" raw port
    raw=$(tr -d '[:space:]' < "$port_file")
    if [[ "$raw" =~ ^[0-9]+$ ]]; then
        port="$raw"
    elif [[ "$raw" =~ \"port\":([0-9]+) ]]; then
        port="${BASH_REMATCH[1]}"
    else
        return 1
    fi
    [ "$port" -ge 1024 ] && [ "$port" -le 65535 ] || return 1
    printf '%s' "$port"
}

_editor_process_running() {
    if command -v tasklist >/dev/null 2>&1; then
        MSYS_NO_PATHCONV=1 tasklist /FI "IMAGENAME eq UnrealEditor.exe" /NH 2>/dev/null | grep -qi "UnrealEditor.exe"
    else
        pgrep -f "UnrealEditor" >/dev/null 2>&1
    fi
}

# Find a live editor port. Preferred signal: valid port file whose MCP health
# probe succeeds. Fallback (only when an editor process is running): probe the
# default bind range (8742 + auto-increment), so "editor up + MCP healthy +
# port file missing" is still treated as ready instead of launching a duplicate.
_find_live_port() {
    local port_file port candidate
    port_file=$(_find_port_file)
    if [ -n "$port_file" ]; then
        port=$(_read_port_from_file "$port_file") || port=""
        if [ -n "$port" ] && _mcp_health_probe "$port"; then
            printf '%s' "$port"; return 0
        fi
    fi
    if _editor_process_running; then
        for candidate in $(seq 8742 8752); do
            if _mcp_health_probe "$candidate"; then
                printf '%s' "$candidate"; return 0
            fi
        done
    fi
    return 1
}

is_editor_ready() {
    [ -n "$(_find_live_port)" ]
}

# ── Fast path ──────────────────────────────────────────────────────────────
if is_editor_ready; then
    exit 0
fi

# ── Parallel guard ─────────────────────────────────────────────────────────
# Another hook instance may already be starting the editor (Claude batches calls).
# Lock dir contains a PID file so stale locks (from killed hooks) are detected.
# Stale = no pid file, empty pid, or dead pid.
_try_acquire_lock() {
    mkdir -p "$PROJECT_DIR/Saved" 2>/dev/null || return 1
    mkdir "$LOCK_DIR" 2>/dev/null || return 1
    # Set cleanup trap immediately — before anything else — so kills during
    # startup never leave a stale lock behind
    trap 'rm -rf "$LOCK_DIR" 2>/dev/null; true' EXIT
    echo $$ > "$LOCK_DIR/pid"
}

if ! _try_acquire_lock; then
    LOCK_PID=$(cat "$LOCK_DIR/pid" 2>/dev/null)
    if [ -z "$LOCK_PID" ] || ! kill -0 "$LOCK_PID" 2>/dev/null; then
        # Stale lock — take over
        rm -rf "$LOCK_DIR"
        _try_acquire_lock || true
    fi
fi

if [ "$(cat "$LOCK_DIR/pid" 2>/dev/null)" != "$$" ]; then
    # Another live instance holds the lock — wait for it to finish (up to 185s)
    WAIT=0
    while [ $WAIT -lt 185 ]; do
        sleep 5; WAIT=$((WAIT + 5))
        is_editor_ready && exit 0
        [ ! -d "$LOCK_DIR" ] && break
    done
    cat >&2 <<'EOF'
Unreal Editor is not running and a startup attempt did not complete.
Tell the user: MCP tools are unavailable. Ask them to choose:
1. Start the editor manually (see CLAUDE.md Open Editor command), then retry
2. Abort the current task
Do not proceed with MCP tool calls until the user chooses.
EOF
    exit 2
fi

# ── Resolve engine path ────────────────────────────────────────────────────
ENGINE_PATH=$(resolve_engine_path) || exit 2

if [ -z "$ENGINE_PATH" ] || [ ! -d "$ENGINE_PATH" ]; then
    cat >&2 <<'EOF'
Unreal Editor is not running and the engine path could not be determined.
Tell the user: MCP tools require the Unreal Editor. Ask them to choose:
1. Run cortex-setup to create .cortex/config.yaml, then configure .cortex/config.local.yaml with engine.path if this machine needs a local override
2. Set the UE_PATH environment variable and retry
3. Start the editor manually (see CLAUDE.md), then retry
4. Abort the current task
Do not proceed with MCP tool calls until the user chooses.
EOF
    exit 2
fi

# Find .uproject
UPROJECT=$(ls "$PROJECT_DIR"/*.uproject 2>/dev/null | head -1)
if [ -z "$UPROJECT" ]; then
    echo "No .uproject file found in $PROJECT_DIR" >&2; exit 2
fi

# Remove stale port files (from a previous crash, Stop() never ran)
rm -f "$PROJECT_DIR/Saved/CortexPort.txt" "$PROJECT_DIR/Saved/CortexPort-"*.txt 2>/dev/null || true

# ── Launch editor ──────────────────────────────────────────────────────────
"$ENGINE_PATH/Engine/Binaries/Win64/UnrealEditor.exe" \
    "$UPROJECT" \
    -nosplash -nopause -AutoDeclinePackageRecovery \
    > /dev/null 2>&1 &
EDITOR_PID=$!
disown $EDITOR_PID

# ── Poll for port file + TCP (180s) ───────────────────────────────────────
# Phase 1 (0-30s): just poll, editor/build tool still loading
# Phase 2 (30-180s): also verify our launched PID is still alive
#
# We track the PID we launched — not process names from tasklist, which
# could match another editor instance from a different project.
# The port file (CortexPort-{PID}.txt or CortexPort.txt) is project-specific,
# so port file + TCP response = proof that OUR editor is ready.

ELAPSED=0
DEADLINE=180
PROCESS_CHECK_AFTER=30

while [ $ELAPSED -lt $DEADLINE ]; do
    sleep 5; ELAPSED=$((ELAPSED + 5))

    if is_editor_ready; then
        if _find_port_file >/dev/null 2>&1; then
            echo "Unreal Editor started and CortexCore TCP server is ready."
        else
            echo "Unreal Editor is running and MCP is reachable (port file missing)."
        fi
        exit 0
    fi

    # Phase 2: verify our launched process is still alive
    if [ $ELAPSED -ge $PROCESS_CHECK_AFTER ]; then
        if ! kill -0 $EDITOR_PID 2>/dev/null; then
            cat >&2 <<'EOF'
The editor process we launched has exited. Check Saved/Logs/ for details.
Tell the user: the editor process exited and MCP tools are unavailable. Ask them to choose:
1. Check the logs and restart the editor manually, then retry
2. Abort the current task
Do not proceed with MCP tool calls until the user chooses.
EOF
            exit 2
        fi
    fi
done

# Timed out — our PID is still alive but no live MCP endpoint was found
if kill -0 $EDITOR_PID 2>/dev/null; then
    cat >&2 <<'EOF'
Unreal Editor is running but CortexCore MCP did not become reachable within 180 seconds.
Tell the user: verify that the UnrealCortex plugin is enabled in the project and
UCortexSettings.bAutoStart is true. Ask them to choose:
1. Fix the configuration and restart the editor, then retry
2. Abort the current task
Do not proceed with MCP tool calls until the user chooses.
EOF
else
    cat >&2 <<'EOF'
The editor process exited before becoming ready.
Tell the user: MCP tools are unavailable. Ask them to choose:
1. Start the editor manually (see CLAUDE.md Open Editor command), then retry
2. Abort the current task
Do not proceed with MCP tool calls until the user chooses.
EOF
fi
exit 2
