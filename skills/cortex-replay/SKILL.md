---
name: cortex-replay
description: Use when replaying a human-enabled CortexReplay recording in editor PIE, checking its run status, or recovering an uncertain replay start.
---

# CortexReplay

AI playback of human-captured physical-input recordings through the `replay` MCP domain (`replay_cmd`).
A human records and grants AI use in the CortexReplay window; this skill only discovers recordings,
starts one AI run, reports its status, and cancels it. It never records, edits, enables, deletes or
reproduces a recording outside the guarded replay path.

Read `resources/replay-workflow.md` before a first run — it carries the operation contract, guard
coverage matrix, response fields and recovery rules.

## Intent Routing

- "what can I replay", "list recordings" -> Discovery Mode
- "replay recording N", "run recording N" -> Run Mode
- "status of run X", "did it finish", "I lost the run" -> Status and Recovery Mode
- "stop/cancel the replay" -> Cancel Mode

If a request mixes starting and checking, run the phases in order. Never start a second run to
"retry" or "confirm" a start whose outcome is already known or recoverable.

## Discovery Mode

1. Call `replay_cmd(command="list_recordings", params={})`. Pages are live and ascending by integer
   `recording_id`, bounded (default 20 rows; `page_size` 1..100). Continue with `after_recording_id`
   set to the returned `next_after_recording_id` while `has_more` is true. Pages are not a snapshot:
   each request rechecks current eligibility, so a library change below the cursor needs a fresh
   first page.
2. Only AI-enabled, complete recordings appear, each with map, recorded start pose and a
   guard-coverage summary. The same response carries `active_ai_run` (the current AI operation, if
   any) and up to 100 `recent_ai_runs` terminal summaries finalized within the last 24 hours
   (`recovery_window_seconds`, `recovery_max_terminal_runs`).
3. Select the exact integer `recording_id` from a row. Never guess an ID, use an array index, a
   name or a timestamp. A guessed valid-but-disabled ID is denied.
4. If a recording is missing or denied, stop and ask the human to enable AI use or fix its coverage
   in the CortexReplay window. There is no parameter, override or self-grant path here.

## Run Mode

1. Confirm the intended recording with
   `replay_cmd(command="get_recording", params={"recording_id": N})`. Read `recording_id`, the
   recorded map, the recorded start pose and `guard_coverage`. If `guard_coverage.ui_unavailable_presses`
   is non-zero the recording has explicit partial coverage: it still replays as pose-guarded,
   press-only input, and the shortfall must be reported, never hidden or "upgraded".
2. Start exactly once: `replay_cmd(command="start_replay", params={"recording_id": N})`. A normal
   success envelope carries `run_id`, `recording_id`, `editor_instance_id` and `state: "Preparing"`.
   Acceptance is not completion.
3. Keep the returned canonical `run_id`, then poll
   `replay_cmd(command="get_run", params={"run_id": "<the returned UUID>"})` until it reports a
   terminal state. Always send the real UUID; never send an explanatory placeholder string.
4. Never issue a second `start_replay` for the same intent. A competing start while the target is
   owned returns busy; a mistaken later start admits a different run and destroys the record of what
   actually happened.

### Preparation and scope

- Replay starts a fresh owned PIE session on the recorded map even when another editor map is open.
  Before input time zero it teleports the recorded pawn class to the recorded world
  location/rotation/scale and restores the controller view rotation, then reads the pose back.
  Teleport here is preparation only — never recorded movement or drift correction.
- The recorded pose is a player-pose starting point, not a checkpoint. Inventory, doors, quests,
  enemy state, velocity and open menus are not restored; flows that need them must establish them
  through recorded input or be re-recorded from a reproducible environment.
- Physical input requires a rendered, correctly focused PIE surface. This release does not promise
  unfocused, hidden-window or NullRHI replay, and the CortexReplay window need not be open.

## Status and Recovery Mode

1. `replay_cmd(command="get_run", params={"run_id": "<uuid>"})` returns the live run or its retained
   terminal result. Terminal states are `Completed`, `Cancelled`, `Interrupted` and `Error`.
   `Completed` means the validated input sequence finished dispatching — not that every event was
   consumed or the feature behaved correctly. Never report gameplay pass/fail from it.
2. An `Error` state is still a successful status query. Read `execution_error.code`, `execution_error.message`
   and `execution_error.details`. Guard failures (`REPLAY_POSE_GUARD_FAILED`,
   `REPLAY_UI_GUARD_FAILED`, `REPLAY_UI_WAIT_TIMEOUT`) carry the affected event `sequence` and
   expected/actual deviation: pose `position_delta_cm`, `pawn_rotation_delta_degrees`,
   `control_rotation_delta_degrees`, `max_scale_delta`; UI `local_error`, `actual_x`, `actual_y`,
   `tolerance`, `observation` and `reason`.
3. **Uncertain start:** if `start_replay` returns `REPLAY_START_OUTCOME_UNKNOWN`
   (`outcome: "unknown"`, `recovery_required: true`), the start was dispatched but its acknowledgement
   was lost. Do NOT reissue start. Recover through the live surface: query `list_recordings` and match
   the recording ID against `active_ai_run` and `recent_ai_runs`, then `get_run` that `run_id`. A run
   that finished before discovery is still found in `recent_ai_runs`. Only
   `REPLAY_START_NOT_DISPATCHED` (`outcome: "not_dispatched"`, `recovery_required: false`) means no run
   was admitted and nothing is outstanding.
4. A terminal result is stable. Querying or cancelling a finalized run returns its actual terminal
   state without another cleanup. If the discovery window (24 hours / 100 summaries) has passed,
   report that recovery is no longer possible; never infer that start was never delivered. If several
   summaries could match, report the ambiguity instead of restarting.

## Cancel Mode

`replay_cmd(command="cancel_replay", params={"run_id": "<uuid>"})` cancels that AI-originated run or
returns its existing terminal state. It releases only replay-owned held input and never cancels a
human capture or playback run.

## Guard, Wait and Coverage Rules

- Guards are press-only. Immediately before each non-repeat key-down, pointer-button-down and
  double-click, the live pose is compared with the recorded pose (≤ 0.5 cm location, ≤ 0.5° pawn and
  control rotation, ≤ 0.001 scale). An identifiable UI press additionally re-resolves its structured
  widget identity and hit-tests the pointer (≤ 0.005 normalized local error). Releases and motion are
  never gated, so a successful guard is not proof that a later click/release/drag effect succeeded.
- A pending or not-yet-ready intended target may be waited for: up to 1 second per press and at most
  5 seconds cumulatively per run, only with neutral input (no replay-owned key/button held, no active
  pointer capture or drag) and continued ownership/focus/eligibility. Waiting never absorbs movement,
  never enlarges tolerances, never clicks a different widget, and never catches up by bursting events.
- On any guard failure the blocked press and every later event are suppressed, replay-owned held
  inputs release exactly once, and the run finalizes `Error` with the deviation evidence. Do not
  retry, nudge movement, teleport after time zero, change a threshold, or re-record the sequence
  yourself.

### Supported UI identity and partial coverage

| Target family | Supported guard identity | Explicitly unavailable |
|---|---|---|
| Screen-space UMG/CommonUI | Authored named pointer controls under a uniquely identified player-owned root; nested authored instances distinguished by authored ancestry | Untagged duplicate roots; virtualized/dynamic instances without a stable authored discriminator |
| Native runtime Slate | Uniquely authored tagged pointer control under a uniquely identified selected runtime root | Untagged anonymous controls; type, caption or index alone is not identity |
| World-space Widget Component | Authored named controls under a saved-map actor and named component with a proven physical hardware-input hit-test route | Runtime-spawned owners without stable identity; virtual-pointer routes with an unprovable device/component or fresh hit |

This matrix is the acceptance contract, not permission to label every target unsupported. A required
target that becomes unavailable at playback is an error, never a silent downgrade. Coverage is fixed
by capture; AI permission does not extend it.

## What This Skill Cannot Do

There are no parameters — and no caller path — for input files, inline sequences, alternate start
positions, guard or tolerance overrides, corrective movement, console commands, playback speed,
assertions, screenshots, recording metadata mutation, permission grants or recording capture.
`replay_cmd` exposes only the five operations above. When a human needs to record, rename, enable,
disable, delete or re-capture a recording, direct them to the CortexReplay window.

**Revocation:** if a human revokes AI permission while a run is active, native cancels only that
still-active AI run and releases its held input. An already-known run's terminal status survives
revocation — you may still read that run's status — but that recording is denied for new
`get_recording`/`start_replay` and disappears from discovery.

## Drift Reporting

When a guard error shows that the recorded pose or UI target no longer matches, the correct output is
a concise report — recording ID, run ID/state, error code, affected event sequence and the
expected/actual deviation — plus a request for the human to re-record from the correct environment.
Do not retry, adjust thresholds, move the player, enable anything, or claim the gameplay succeeded.

## Progress Discipline

- Retry a failed read once with corrected parameters; never retry a start.
- After 3 failed calls, or 3 calls with no meaningful progress, stop and report what blocked you.
- Always report the final run `state`, and for `Error` the structured deviation.
