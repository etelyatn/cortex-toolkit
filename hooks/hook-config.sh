#!/usr/bin/env bash
# Shared gate for Cortex agent hooks (cortex-toolkit issue #63).
#
# Agent hooks are opt-in. This library resolves the effective value of the
# hooks.* switches from the project config and is deliberately dependency-free
# (no python, no Editor, no network) so the disabled path is a cheap,
# side-effect-free early exit on every host.
#
# Configuration, in the project's .cortex directory:
#   config.yaml        hooks: { editor_guard: <bool>, session_context: <bool> }
#   config.local.yaml  per-machine override; wins for the keys it defines
#
# Missing project, missing config, missing key, or an unrecognized value all
# mean "disabled".

# Print the nearest project directory: $CLAUDE_PROJECT_DIR when set, otherwise
# the closest ancestor of the current (or script) directory containing a
# .uproject file or a .cortex directory. Returns non-zero when none is found.
cortex_project_dir() {
    local start
    if [ -n "${CLAUDE_PROJECT_DIR:-}" ] && [ -d "$CLAUDE_PROJECT_DIR" ]; then
        printf '%s\n' "$CLAUDE_PROJECT_DIR"
        return 0
    fi
    for start in "$(pwd)" "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." 2>/dev/null && pwd)"; do
        [ -n "$start" ] || continue
        if cortex_walk_up_for_project "$start"; then
            return 0
        fi
    done
    return 1
}

# Walk up from a directory (at most 20 levels) looking for a project marker.
cortex_walk_up_for_project() {
    local dir="$1" parent
    for _ in $(seq 1 20); do
        if compgen -G "$dir/*.uproject" >/dev/null 2>&1 || [ -d "$dir/.cortex" ]; then
            printf '%s\n' "$dir"
            return 0
        fi
        parent=$(dirname "$dir")
        [ "$parent" = "$dir" ] && break
        dir="$parent"
    done
    return 1
}

# Print the raw value assigned to key in a Cortex config file (last match).
cortex_config_raw_value() {
    local file="$1" key="$2"
    [ -f "$file" ] || return 0
    sed -n "s/^[[:space:]]*$key[[:space:]]*:[[:space:]]*\([^#[:space:]]*\).*/\1/p" "$file" | tail -n 1
}

# Return 0 when the effective hooks.<key> switch is truthy; 1 otherwise.
cortex_hook_enabled() {
    local key="$1" dir value
    dir=$(cortex_project_dir) || return 1
    value=$(cortex_config_raw_value "$dir/.cortex/config.local.yaml" "$key")
    [ -n "$value" ] || value=$(cortex_config_raw_value "$dir/.cortex/config.yaml" "$key")
    case "$value" in
        true|True|TRUE|yes|Yes|YES|on|On|ON|1) return 0 ;;
        *) return 1 ;;
    esac
}
