# Replay Domain Context

<!-- Human-enabled CortexReplay recording library and guarded AI replay conventions for CortexReplay -->

## What CortexReplay Does

`CortexReplay` exposes the `replay` MCP domain for replaying human-captured physical-input
recordings inside editor PIE. A human records and grants AI use in the CortexReplay window;
the AI command surface only discovers eligible recordings, starts one guarded AI run, reads
its status and cancels it. There is no AI recording, editing, permission or delete path.

## Commands

| Command | Purpose |
|---------|---------|
| `replay.list_recordings` | Live eligible recording page (ascending ID) with map, prerequisites and guard-coverage summary (no start pose), the active AI run and recent terminal AI-run summaries. Paged by `after_recording_id` / `page_size`. |
| `replay.get_recording` | One eligible recording's metadata, `initial_state` (recorded pawn transform and control rotation) and guard-coverage warning. |
| `replay.start_replay` | Accept one AI replay run and return its `Preparing` identity (`run_id`). One-shot; never inside a Core batch and never resent. |
| `replay.get_run` | Live AI run state or retained terminal result. |
| `replay.cancel_replay` | Cancel that AI-originated run or return its existing terminal state. |

## Boundaries

Use this domain for human-enabled recordings only. Do not use it to record, rename, enable,
delete or re-capture a recording, and do not attempt input files, inline sequences, alternate
start positions, guard/tolerance overrides, console commands, playback speed, assertions or
screenshots — none of those parameters exist. Direct the human to the CortexReplay window for
anything outside discovery, start, status and cancel.

Physical replay requires a rendered, correctly focused PIE surface; unfocused, hidden-window
and NullRHI replay are not promised. The recorded pose is a starting point, not a checkpoint.

## Guard Coverage

Guards are press-only and fixed by capture: pose tolerance 0.5 cm / 0.5° / 0.001 scale, and
0.005 normalized UI local-position error. Capture-reported coverage is
`pose_presses`, `ui_supported_presses`, `ui_unavailable_presses`, `ui_not_applicable_presses`.
A recording with unavailable UI-target presses has explicit partial coverage and must be
reported, not hidden.

## Recovery

`replay.start_replay` may return `REPLAY_START_OUTCOME_UNKNOWN` when the start was dispatched
but its acknowledgement was lost; recover the admitted run through `list_recordings`
(`active_ai_run` / `recent_ai_runs`) and `get_run`, and never reissue start.
`REPLAY_START_NOT_DISPATCHED` means no run was admitted.

## Project Notes

<!-- WHY: The AI needs to know which recordings exist for this project and what each requires
     so it can choose the right one and report the correct partial coverage.

     Record the human-enabled recordings this project expects to replay here — integer ID,
     short purpose, recorded map and any guard-coverage warning. Example:

     - #103 "Pause menu" — /Game/Maps/TestMap; menu press on an authored tagged Slate control, so it
       is UI-guarded on the shipped tagged-Slate route
     - #104 "Door interaction" — /Game/Maps/TestMap; pose-only coverage (screen-space UMG button with
       no tagged-Slate identity, so capture marks it ui_guard_unavailable)
-->

## Environment

<!-- WHY: Replay depends on the editor/PIE target and prerequisites that capture recorded.
     Describe how to reach a state the recordings expect.

     Example:
     - Default replay map: /Game/Maps/TestMap with the normal player start
     - Recordings assume the editor is focused and the PIE viewport is rendered
     - Establish pre-existing game state (inventory, doors, quests) through recorded input;
       replay does not restore it
-->

## Approved Flows

<!-- WHY: The AI should start only the flows the project has deliberately enabled for AI use.

     Example:
     - Smoke: replay #103, expect Completed, then a human verifies the menu opened
     - Regression: replay #104 (pose-only) for the door interaction; expect Completed, or a
       pose-guard Error if the door no longer starts where it was recorded
-->

## Drift / Known Issues

<!-- WHY: Prevents repeated failed replays when a recording no longer matches the current
     environment. Note recordings that need re-recording and why.

     Example:
     - #103 fails with REPLAY_UI_GUARD_FAILED local_position_mismatch after the menu layout change
       on 2026-10-04 — its tagged Slate control moved; needs human re-recording
     - #104 (pose-only) fails with REPLAY_POSE_GUARD_FAILED position_delta_cm after the door moved —
       needs human re-recording
-->
