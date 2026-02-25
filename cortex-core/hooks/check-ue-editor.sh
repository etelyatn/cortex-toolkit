#!/usr/bin/env bash
# PreToolUse guard: ensure Unreal Editor + CortexCore TCP are ready
# before any cortex_mcp tool call.
#
# Fast path (~50ms): port file valid + TCP responds → exit 0 silently
# Start path: lock-protected editor launch, 180s two-phase poll
# Fail path: exit 2 with Claude-directive stderr

set -uo pipefail

LOCK_DIR="/tmp/cortex-ue-editor-starting.lock"

# Resolve project root: prefer CLAUDE_PROJECT_DIR, then search upward from pwd for .uproject
_find_project_dir() {
    if [ -n "${CLAUDE_PROJECT_DIR:-}" ] && [ -d "$CLAUDE_PROJECT_DIR" ]; then
        echo "$CLAUDE_PROJECT_DIR"; return 0
    fi
    local dir
    dir=$(pwd)
    for _ in $(seq 1 20); do
        if ls "$dir"/*.uproject 2>/dev/null | head -1 | grep -q .; then
            echo "$dir"; return 0
        fi
        local parent
        parent=$(dirname "$dir")
        [ "$parent" = "$dir" ] && break
        dir="$parent"
    done
    return 1
}

PROJECT_DIR=$(_find_project_dir) || PROJECT_DIR="${CLAUDE_PROJECT_DIR:-.}"
RESTART_LOCK="$PROJECT_DIR/Saved/CortexRestarting.lock"

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

# Validate port file and check TCP using bash built-in /dev/tcp (no external tools needed)
is_editor_ready() {
    local port_file
    port_file=$(_find_port_file) || return 1
    local raw port
    raw=$(tr -d '[:space:]' < "$port_file")
    # Support both plain-number and JSON {"port":N,...} formats
    if [[ "$raw" =~ ^[0-9]+$ ]]; then
        port="$raw"
    elif [[ "$raw" =~ \"port\":([0-9]+) ]]; then
        port="${BASH_REMATCH[1]}"
    else
        return 1
    fi
    [ "$port" -ge 1024 ] && [ "$port" -le 65535 ] || return 1
    (echo >/dev/tcp/127.0.0.1/$port) 2>/dev/null
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
ENGINE_PATH="${UE_56_PATH:-}"
if [ -z "$ENGINE_PATH" ] && [ -f "$PROJECT_DIR/.cortex/config.yaml" ]; then
    ENGINE_PATH=$(grep -E '^\s+path:' "$PROJECT_DIR/.cortex/config.yaml" \
        | head -1 | sed 's/.*path:[[:space:]]*//' | tr -d '"'"'" | tr -d '\r')
fi

if [ -z "$ENGINE_PATH" ] || [ ! -d "$ENGINE_PATH" ]; then
    cat >&2 <<'EOF'
Unreal Editor is not running and the engine path could not be determined.
Tell the user: MCP tools require the Unreal Editor. Ask them to choose:
1. Set the UE_56_PATH environment variable and retry
2. Start the editor manually (see CLAUDE.md), then retry
3. Abort the current task
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
        echo "Unreal Editor started and CortexCore TCP server is ready."
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

# Timed out — our PID is still alive but port file never appeared
if kill -0 $EDITOR_PID 2>/dev/null; then
    cat >&2 <<'EOF'
Unreal Editor is running but CortexCore did not write a port file within 180 seconds.
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
