# CortexReplay Workflow Reference

> Reference guide — replay operation contract and recovery rules, not an agent definition. Loaded by the `cortex-replay` skill.

CortexReplay plays back a human-captured physical-input recording inside editor PIE through the
`replay` MCP domain. A human authors and enables recordings in the CortexReplay window; the AI
command surface only discovers, starts, reports and cancels AI-originated runs. The toolkit is
skills-only: this guide describes the shipped MCP operations and their native contract.

## Operations

All five operations go through `replay_cmd(command="...", params={...})`. Commands and parameters are
identical in native parsing, the MCP boundary and live capabilities.

| Command | Parameters | Result |
|---|---|---|
| `list_recordings` | `after_recording_id` (optional, positive int32), `page_size` (optional, 1..100, default 20) | Live eligible recording page, ascending ID, each row with map, recorded start pose and guard-coverage summary; `has_more`, `next_after_recording_id`, `editor_instance_id`, `active_ai_run` and `recent_ai_runs` |
| `get_recording` | `recording_id` (required, positive int32) | Eligible recording metadata, recorded start pose and guard-coverage warning; no input rows or arbitrary file access |
| `start_replay` | `recording_id` (required, positive int32) | Synchronous acceptance: `run_id`, `recording_id`, `editor_instance_id`, `state: "Preparing"` |
| `get_run` | `run_id` (required, canonical lower-case UUID) | Live AI run state or retained terminal result with progress, wait substate and error details |
| `cancel_replay` | `run_id` (required, canonical lower-case UUID) | Cancels that AI-originated run or returns its existing terminal state |

Only `list_recordings` accepts the two paging fields. Generic `limit`/`cursor`/`offset`/`page`
pagination is rejected before any cursor shortcut. Recording IDs are positive signed 32-bit integers
(1..2147483647); booleans, numeric strings, fractional/zero/negative/out-of-range values are rejected
in Python and again natively. `run_id` must be a canonical, non-nil, lower-case hyphenated UUID.

`start_replay` is one-shot. It is dispatched through the dedicated single-send path, refused inside a
Core `batch`/`batch_query`, and never silently retried. The other operations are ordinary live reads
or idempotent cancellation.

## Run states

`Preparing -> Replaying -> Finalizing`, with terminal results `Completed`, `Cancelled`, `Interrupted`
or `Error`. Readiness waiting is a `Replaying` substate (reported in `waiting`), not a second
operation. One operation owns the selected target at a time; a competing start returns busy.

`Completed` means the validated input sequence finished dispatching without an execution
interruption or error. It is not a gameplay pass/fail verdict, and there is no `passed` field or
assertion count. `Error` is returned inside a successful status query (`get_run`) as
`execution_error`; a missing/unauthorized/invalid run is a normal command error instead.

## Discovery, selection and paging

- Discovery returns only AI-enabled, complete recordings. Eligibility is checked before preparation
  and again before dispatch.
- Pages are live, not an atomic snapshot; each request rechecks eligibility. A change below an
  already-traversed ID requires a fresh first page. A page may return fewer rows than `page_size` to
  stay within its encoded-size budget, but never silently truncates a row or a declared recovery
  summary.
- `recent_ai_runs` carries up to 100 terminal AI-run summaries finalized within the preceding 24
  hours (newest first), each with `run_id`, `recording_id`, `editor_instance_id`, start/finalize UTC
  times and `state`. `active_ai_run` is the current AI operation, if any.
- These summaries describe execution diagnostics only; they never expose recorded input payloads, and
  `get_recording` still requires current eligibility.

## Uncertain start recovery

The MCP boundary distinguishes two start failures:

- `REPLAY_START_NOT_DISPATCHED` — `outcome: "not_dispatched"`, `recovery_required: false`. The start
  never reached the native service; no run was admitted.
- `REPLAY_START_OUTCOME_UNKNOWN` — `outcome: "unknown"`, `recovery_required: true`. The start was
  dispatched but its acknowledgement was lost. The run may exist.

On an unknown outcome, recover the admitted run through live discovery — query `list_recordings` and
match the recording ID against `active_ai_run` and `recent_ai_runs`, then `get_run` that `run_id`.
Never reissue `start_replay`. A run that finished or failed preparation before reconnection is still
found in `recent_ai_runs` within the 24-hour / 100-summary window; outside it, report that recovery is
no longer possible rather than assuming the start never happened. Ambiguous matches are reported, not
restarted. Reconnecting transport clients keep query/cancel access to AI-originated runs; ownership
is the native human/AI invocation class, not the socket.

## Preparation and start state

- Replay starts a fresh owned PIE session on the recorded map (preferring the PIE map override over
  switching the editor's editing world), even when another map is open. It never interrupts unrelated
  PIE and never discards unsaved editor work.
- Before input time zero, it verifies the recorded pawn class and restores the recorded world
  location/rotation/scale plus the controller view rotation when they differ beyond the fixed
  tolerances, then reads the pose back and fails preparation on a mismatch. Teleport is permitted
  only for this one-time preparation — never as recorded movement or drift correction.
- Prerequisites (map/content, pawn class, target/focus, eligibility) are resolved before dispatch and
  rechecked before the first dispatch after PIE readiness.
- The recorded pose is a player-pose starting point, not a checkpoint: fresh PIE does not reproduce
  inventory, doors, quests, enemy state, earlier triggers, velocity or open menus.

## Guards, waits and coverage

Automatic interaction guards are press-only. Immediately before each non-repeat key-down,
pointer-button-down and double-click, native captures and compares the live pose against the recorded
guard:

| Guard | Tolerance |
|---|---|
| Euclidean location error | ≤ 0.5 cm |
| Pawn / control-rotation shortest quaternion angular error (each) | ≤ 0.5° |
| Maximum scale-component error | ≤ 0.001 |
| UI normalized local x/y absolute error | ≤ 0.005 |

For an identifiable UI pointer press the guard also resolves the recorded structured widget identity
and hit-tests the live pointer against it after preceding motion is processed. Visibility, enabled
state and hit-testability are required. A different actionable widget is an immediate mismatch; the
pointer is never relocated and the click is never retargeted. Releases, cleanup releases and motion
are not gated, so press protection does not promise that a later OnClicked/OnReleased/drag action
succeeded — this press-only limit is surfaced in the recording popup, AI metadata and run results.

When a required UI target is missing, not yet ready, or its layout/input processing is pending, replay
may wait up to 1 second per press and at most 5 seconds cumulatively per run — only with neutral input
(no replay-owned key/button held, no active pointer capture or drag) and continued ownership, focus
and eligibility. Explicit readiness waits pause only the replay timeline and shift later deadlines by
the measured wait; events are never burst, skipped or compressed afterwards.

Capture records guard coverage as counts: `pose_presses`, `ui_supported_presses`,
`ui_unavailable_presses`, `ui_not_applicable_presses` (the response adds `guard_scope: "press_only"`).
A press whose reproducible widget identity cannot be obtained is marked `ui_guard_unavailable` and
keeps only its pose guard — that is explicit partial coverage, surfaced as a warning. A previously
supported identity becoming unavailable at playback is an error, never an automatic downgrade.
Coverage is fixed by capture; AI permission does not upgrade it.

### Supported UI identity matrix

| Target family | Required guard support | Explicitly unavailable cases |
|---|---|---|
| Screen-space UMG/CommonUI | Authored named Button/Slider and other pointer controls under a uniquely identified player-owned root; nested authored instances distinguished by ancestry | Untagged duplicate roots; virtualized/dynamic instances without an authored stable discriminator |
| Native runtime Slate | Uniquely authored tagged pointer control under a uniquely identified selected runtime root | Untagged anonymous controls; type/caption/index alone is not identity |
| World-space Widget Component | Authored named controls under a saved-map actor and named component with a proven physical hardware-input hit-test route | Runtime-spawned owners without stable identity; virtual-pointer routes whose selected device/component or fresh hit cannot be proven |

These rows are acceptance obligations, not permission to label every target unsupported.

## Guard failure diagnostics

A guard failure finalizes the run `Error`, suppresses the blocked press and every later event, and
releases replay-owned held input exactly once. `execution_error.details` is bounded and carries the
affected event `sequence`, kind, guard type and the expected/actual evidence:

- `REPLAY_POSE_GUARD_FAILED` — `position_delta_cm`, `pawn_rotation_delta_degrees`,
  `control_rotation_delta_degrees`, `max_scale_delta` against the fixed tolerances.
- `REPLAY_UI_GUARD_FAILED` — `reason` (`identity_mismatch`, `local_position_mismatch`,
  `unequivocal_mismatch`, `wait_not_permitted`, `missing_expected_selector`), `observation`,
  `tolerance`, `local_error`, `actual_x`, `actual_y` and `expected_identity_sha256`.
- `REPLAY_UI_WAIT_TIMEOUT` — the readiness budget expired before the press could be dispatched.
- `REPLAY_TIMING_ERROR` — dispatch lateness exceeded the fixed 100 ms accidental-lateness bound;
  `sequence` and `lateness_ms` identify the affected event.

Agents report drift with this evidence and ask the human to re-record; they do not retry, nudge,
change thresholds, teleport after time zero, or edit the recording.

## AI authorization and revocation

- `ai_enabled` lives in tracked recording metadata and travels with the recording. New and incomplete
  recordings are never enabled by default; only the human Edit popup's Save changes it.
- AI discovery omits non-enabled recordings, and explicit ID lookup or playback of a non-enabled
  record is denied even when the caller guesses a valid ID.
- Revoking permission while an AI run is active cancels only that still-active AI run and releases its
  held input; it does not cancel an unrelated human run. An already-known run's terminal status (and
  its recovery summary) survives revocation and deletion — but the recording is denied for new
  `get_recording`/`start_replay` and new playback.
- There is no caller-supplied `source=human` switch and no authoring/self-grant bypass, including
  through Core batch routing.

## Non-existent parameters

There are no parameters — and no caller path — for input files, inline sequences, alternate start
positions, guard/tolerance overrides, corrective movement, console commands, playback speed,
assertions, screenshots, or recording metadata mutation. Normal-speed replay is the only mode.
Recording capture, rename, enable/disable and delete are human-only actions in the CortexReplay
window; existing user files under the legacy QA recording directories are preserved and never
converted or auto-imported.

## Storage

```text
<Project>/.cortex/replay/
  library.json                  # library schema version and next_recording_id
  recordings/<id>/
    metadata.json               # identity, permission, map, prerequisites, hashes
    initial_state.json          # immutable player transform and view rotation
    inputs.jsonl                # immutable ordered events and automatic guards
<Project>/Saved/CortexReplay/
  Runs/                         # local per-run execution results and diagnostics
  Temp/                         # uncommitted capture/write scratch
```

Recording files under `.cortex/replay/` are intended for Git tracking in the project (not the plugin
submodule); local runs, temp state and logs stay under `Saved/`. Replaying on another machine creates
a local result, never a dirty tracked recording. Legacy `Saved/CortexQA/Recordings/` and
`Saved/CortexQARecordings/` files are retained unchanged and are not valid physical-input recordings.
