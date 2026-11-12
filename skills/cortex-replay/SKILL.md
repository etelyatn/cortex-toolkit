---
name: cortex-replay
description: Use when listing, replaying or validating a human-enabled CortexReplay recording in editor PIE (does recording N still replay?), checking its run status, or recovering an uncertain replay start.
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
- "validate recording N", "does N still replay", "check the recordings" -> Validate Mode
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
2. Only AI-enabled, complete recordings appear, each with map, `duration_seconds` (the recorded
   length), `created_at_utc` (when it was recorded), prerequisites and a guard-coverage summary.
   When listing for a human, show ID, name, map, length and recording date. A list row does **not**
   carry the recorded pose — read `get_recording`'s `initial_state` for the pawn transform and
   control rotation. The same response carries `active_ai_run` (the current
   AI operation, if any) and up to 100 `recent_ai_runs` terminal summaries finalized within the last
   24 hours (`recovery_window_seconds`, `recovery_max_terminal_runs`).
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
- Unless the recording's `countdown_enabled` is false, every run waits a 3-second hands-off
  countdown after the target is ready (`start_replay` returns `countdown_seconds`; `get_run` reports
  `phase: "countdown"` with `countdown_remaining_seconds`, then `phase: "playback"`). The human sees
  a countdown on the game view and a "Replaying…" banner; do not treat the countdown as a stall.
- Replay is frame-locked: each recorded frame is one engine frame with one world tick at its recorded
  delta, and the editor uses fixed application stepping during an owned replay (restored at every
  terminal path). There are no wall-clock deadlines. Admission refuses with
  `INCOMPATIBLE_PREREQUISITES` if the editor is already in fixed-step, benchmarking or
  fixed-frame-rate mode, a custom time step is installed or `t.OverrideFPS` is set; readiness also
  refuses a viewport size, DPI, input config or viewport mouse-capture/high-precision state that
  differs from the recording (`details.field` names it; `get_recording.prerequisites` and
  `initial_state.viewport` carry the recorded values). Do not change those settings yourself; ask
  the human. Slate "responsive mode" (dragging an editor control) does not affect a run.

## Validate Mode

Validation answers one question: does this recording still replay faithfully in this project and
editor? It is Run Mode plus a verdict built only from fields the run reports.

1. `get_recording` for the exact ID. Keep `recording_snapshot_sha256`, `duration_seconds`,
   `created_at_utc` and `guard_coverage`.
2. Start exactly once and poll `get_run` to a terminal state (Run Mode steps 2-4). Do not validate
   several recordings concurrently: one operation owns the editor, and a second start returns
   `EDITOR_BUSY`. Validate a list sequentially, one terminal run before the next start.
3. Verdict:

   | Verdict | Condition (all must hold) |
   |---|---|
   | **Replays faithfully** | `state == "Completed"`, `execution_error == null`, `completed_frames == frame_count`, `dispatched_events == total_events`, and the run's `recording_snapshot_sha256` equals the one from step 1 |
   | **Drifted — re-record** | `Error` with `REPLAY_POSE_GUARD_FAILED`, `REPLAY_UI_GUARD_FAILED`, `REPLAY_UI_WAIT_TIMEOUT` or `REPLAY_TIMEBASE_LOST` |
   | **Not validated (environment)** | a preparation/environment code (see Status and Recovery Mode step 3), or `Cancelled`/`Interrupted` |

   An environment verdict says nothing about the recording; report the code and its action, never
   retry in a loop.
4. Report, per recording: ID, name, length, recording date, run ID, verdict, frames
   (`completed_frames`/`frame_count`), events (`dispatched_events`/`total_events`),
   `behind_seconds`, and the guard coverage, stating `ui_unavailable_presses` as partial coverage.
   For a drift verdict include the structured deviation from `execution_error.details`.
5. A faithful replay is **not** a gameplay verdict. Replay ends its owned PIE when the run finalizes
   and has no assertions; never claim the feature works from `Completed`. If the human wants a
   gameplay check, say it needs a separate QA scenario (`cortex-qa`).

## Status and Recovery Mode

1. `replay_cmd(command="get_run", params={"run_id": "<uuid>"})` returns the live run or its retained
   terminal result. Terminal states are `Completed`, `Cancelled`, `Interrupted` and `Error`.
   `Completed` means the validated input sequence finished dispatching — not that every event was
   consumed or the feature behaved correctly. Never report gameplay pass/fail from it.
2. An `Error` state is still a successful status query. Read `execution_error.code`,
   `execution_error.message` and `execution_error.details`. A `Cancelled` or `Interrupted` run also
   carries `execution_error` whenever it has a cause (`PERMISSION_DENIED` after revocation,
   `TARGET_UNAVAILABLE`, `REPLAY_INTERRUPTED_BY_INPUT` for someone using the mouse or keyboard,
   `INVALID_OPERATION` for focus loss, target loss or a replaced pawn/controller); `Completed` has
   none. Its `message` is a fixed human title such as `Replay stopped: you moved the mouse`. Guard
   details are per-code, not a uniform envelope:
   `REPLAY_POSE_GUARD_FAILED` carries `position_delta_cm`, `pawn_rotation_delta_degrees`,
   `control_rotation_delta_degrees` and `max_scale_delta`; `REPLAY_UI_GUARD_FAILED` carries `reason`,
   `observation`, `tolerance`, `local_error`, `actual_x`, `actual_y` and (only when an expected
   selector exists) `expected_identity_sha256`; `REPLAY_UI_WAIT_TIMEOUT` carries no `details` (its
   message names the blocked event sequence). `REPLAY_TIMEBASE_LOST` means a replayed frame did not
   run with its recorded time step. `REPLAY_TIMING_ERROR` (invalid replay clock observation; a healthy
   editor does not emit it) carries `sequence`; no other code puts an event `sequence` in `details`,
   so do not infer a missing sequence, kind or guard type from other counters. Lateness is not an
   error: `behind_seconds` (≥ 0) is the lag at the last paced frame, so a slow host falls behind
   instead of failing.
3. **Preparation and environment errors** (`EDITOR_BUSY`, `ASSET_NOT_FOUND`,
   `INPUT_PREPARATION_TIMEOUT`, `INPUT_POSE_MISMATCH`, `INITIAL_POSE_RESTORE_FAILED`,
   `INPUT_CLEANUP_FAILED`, `INCOMPATIBLE_PREREQUISITES`, `PERMISSION_DENIED`, `TARGET_UNAVAILABLE`)
   are facts about the editor or machine, not gameplay verdicts. Look the code up in the table in
   `resources/replay-workflow.md`, report it with the action it names (usually asking the human to
   stop PIE, fix a setting or re-record) and never retry in a loop.
4. **Uncertain start:** if `start_replay` returns `REPLAY_START_OUTCOME_UNKNOWN`
   (`outcome: "unknown"`, `recovery_required: true`), the start was dispatched but its acknowledgement
   was lost. Do NOT reissue start. Recover through the live surface: query `list_recordings` and match
   the recording ID against `active_ai_run` and `recent_ai_runs`, then `get_run` that `run_id`. A run
   that finished before discovery is still found in `recent_ai_runs`. Only
   `REPLAY_START_NOT_DISPATCHED` (`outcome: "not_dispatched"`, `recovery_required: false`) means no run
   was admitted and nothing is outstanding.
5. A terminal result is stable. Querying or cancelling a finalized run returns its actual terminal
   state without another cleanup. If the discovery window (24 hours / 100 summaries) has passed,
   report that recovery is no longer possible; never infer that start was never delivered. If several
   summaries could match, report the ambiguity instead of restarting.

## Cancel Mode

`replay_cmd(command="cancel_replay", params={"run_id": "<uuid>"})` requests cancellation of that
AI-originated run. The response is the run's state right after the request: `Finalizing` while the
owned PIE teardown is still in flight, or the terminal state. Poll `get_run` until the state is
terminal; a finalized run returns its existing terminal state. It releases only replay-owned held
input and never cancels a human capture or playback run.

## Guard, Wait and Coverage Rules

- Guards are press-only. Immediately before each non-repeat key-down, pointer-button-down and
  double-click, the live pose is compared with the recorded pose (≤ 0.5 cm location, ≤ 0.5° pawn and
  control rotation, ≤ 0.001 scale). A press on the shipped **tagged runtime Slate** route additionally
  re-resolves its tagged widget identity and hit-tests the pointer (≤ 0.005 normalized local error);
  a press whose UI identity is unavailable carries only the pose guard and is reported as partial
  coverage. Releases and motion are never gated, so a successful guard is not proof that a later
  click/release/drag effect succeeded.
- A pending or not-yet-ready intended target may be waited for: up to 1 second per press and at most
  5 seconds cumulatively per run, only with neutral input (no replay-owned key/button held, no active
  pointer capture or drag) and continued ownership/focus/eligibility. Waiting never absorbs movement,
  never enlarges tolerances, never clicks a different widget, and never catches up by bursting events.
- On any guard failure the blocked press and every later event are suppressed, replay-owned held
  inputs release exactly once, and the run finalizes `Error` with the deviation evidence. Do not
  retry, nudge movement, teleport after time zero, change a threshold, or re-record the sequence
  yourself.

### UI identity: tagged runtime Slate only (partial coverage)

The shipped capture and playback route supports exactly one UI guard identity: a uniquely **authored
tagged runtime Slate** pointer control — an authored unique root tag plus an authored unique target
tag under the selected runtime root. Capture resolves it at each pointer-down/double-click boundary;
playback re-resolves and hit-tests the same tagged Slate target.

Everything else is unavailable in this release:

| Target | Status |
|---|---|
| Authored tagged runtime Slate pointer control under a uniquely identified selected runtime root | **Supported** — guarded |
| Untagged/anonymous Slate controls; type, caption or index alone | Unavailable — not an identity |
| Screen-space UMG/CommonUI (including nested authored instances) | Unavailable — capture marks each press `ui_guard_unavailable` (`unobservable_pointer_route`); only the pose guard applies |
| World-space Widget Component / saved-actor routes | Unavailable — same partial-coverage marking; no UI-target protection is claimed |

UMG/CommonUI and world-space Widget Component identity are **planned acceptance obligations for a
later release, not available now** — never promise or imply that a recording's UI press is protected
on those routes.

A recording with unavailable UI-target presses has explicit partial coverage and must be reported,
never hidden or "upgraded". If a previously supported tagged-Slate target becomes unavailable at
playback it is an error, never a silent downgrade; coverage is fixed by capture and AI permission
does not extend it.

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
a concise report — recording ID, run ID/state, error code and the expected/actual deviation the error
does provide — plus a request for the human to re-record from the correct environment. Include an
affected event sequence only when the error supplies one (`REPLAY_TIMING_ERROR`); pose and UI guard
errors do not, so do not invent one. `REPLAY_TIMEBASE_LOST` means a frame did not run with its recorded
time step; report it as drift evidence and do not retry.
Do not retry, adjust thresholds, move the player, enable anything, or claim the gameplay succeeded.

## Progress Discipline

- Retry a failed read once with corrected parameters; never retry a start.
- After 3 failed calls, or 3 calls with no meaningful progress, stop and report what blocked you.
- Always report the final run `state`, and for `Error` the structured deviation.
