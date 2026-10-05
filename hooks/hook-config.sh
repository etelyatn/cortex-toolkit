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

# Look up key in a Cortex config file. Prints "present:<value>" (the value may be
# empty) when the key line exists, and nothing when the file or key is absent, so
# callers can tell a present-but-empty/empty-scalar key apart from a missing key.
cortex_config_raw_value() {
    local file="$1" key="$2" value
    [ -f "$file" ] || return 0
    grep -q "^[[:space:]]*$key[[:space:]]*:" "$file" 2>/dev/null || return 0
    value=$(sed -n "s/^[[:space:]]*$key[[:space:]]*:[[:space:]]*\([^#[:space:]]*\).*/\1/p" "$file" | tail -n 1)
    printf 'present:%s\n' "$value"
}

# Return 0 when the effective hooks.<key> switch is truthy; 1 otherwise.
cortex_hook_enabled() {
    local key="$1" dir value
    dir=$(cortex_project_dir) || return 1
    value=$(cortex_config_raw_value "$dir/.cortex/config.local.yaml" "$key")
    # A present marker wins even when the local value is empty (empty => disabled);
    # fall through to config.yaml only when config.local.yaml does not define the key.
    [ -n "$value" ] || value=$(cortex_config_raw_value "$dir/.cortex/config.yaml" "$key")
    case "$value" in
        present:true|present:True|present:TRUE|present:yes|present:Yes|present:YES|present:on|present:On|present:ON|present:1) return 0 ;;
        *) return 1 ;;
    esac
}
