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
| `list_recordings` | `after_recording_id` (optional, positive int32), `page_size` (optional, 1..100, default 20) | Live eligible recording page, ascending ID; each row carries map, prerequisites and guard-coverage summary (**no start pose** — read `get_recording.initial_state`); `has_more`, `next_after_recording_id`, `editor_instance_id`, `active_ai_run` and `recent_ai_runs` |
| `get_recording` | `recording_id` (required, positive int32) | Eligible recording metadata, `initial_state` (recorded pawn transform, control rotation and viewport state), `prerequisites` (`local_player_index`, `viewport_size`, `dpi_scale`, `player_input_class`, `input_config_sha256`) and `guard_coverage` counts; no input rows or arbitrary file access. Correlate a run with its recording through `recording_snapshot_sha256` |
| `start_replay` | `recording_id` (required, positive int32) | Synchronous acceptance: `run_id`, `recording_id`, `editor_instance_id`, `state: "Preparing"`, `countdown_seconds` (3). Playback begins only after that hands-off countdown |
| `get_run` | `run_id` (required, canonical lower-case UUID) | Live AI run state or retained terminal result with progress, `behind_seconds`, wait substate and error details |
| `cancel_replay` | `run_id` (required, canonical lower-case UUID) | Requests cancellation of that AI-originated run; returns its state right after the request — `Finalizing` or the terminal state. Poll `get_run` until terminal |

Only `list_recordings` accepts the two paging fields. Generic `limit`/`cursor`/`offset`/`page`
pagination is rejected before any cursor shortcut. Recording IDs are positive signed 32-bit integers
(1..2147483647); booleans, numeric strings, fractional/zero/negative/out-of-range values are rejected
in Python and again natively. `run_id` must be a canonical, non-nil, lower-case hyphenated UUID.

`start_replay` is one-shot. It is dispatched through the dedicated single-send path, refused inside a
Core `batch`/`batch_query`, and never silently retried. The other operations are ordinary live reads
or idempotent cancellation.

## Run states

`Preparing -> Replaying -> Finalizing`, with terminal results `Completed`, `Cancelled`, `Interrupted`
or `Error`. A 3-second hands-off countdown runs inside `Preparing` (after target readiness, before pose restore and playback); a target that became ready within the 30 s preparation deadline always gets its full countdown, and it does not count against the frame clock or `authorized_wait_seconds`. While a run is active, `get_run` reports `phase` (`countdown` or `playback`; absent before the target is ready and while Finalizing) and, during the countdown only, `countdown_remaining_seconds`; terminal records carry neither. Readiness waiting is a `Replaying` substate (reported in `waiting`), not a second
operation. One operation owns the selected target at a time; a competing start returns `EDITOR_BUSY`.

`Completed` means the validated input sequence finished dispatching without an execution
interruption or error. It is not a gameplay pass/fail verdict, and there is no `passed` field or
assertion count. `Error` is returned inside a successful status query (`get_run`) as
`execution_error`; a missing/unauthorized/invalid run is a normal command error instead.
`execution_error` (`code`, `message`, optional `details`) is required for `Error`, is present for
`Cancelled` and `Interrupted` whenever the run has a cause (`PERMISSION_DENIED` after revocation,
`TARGET_UNAVAILABLE`, `REPLAY_INTERRUPTED_BY_INPUT`, or `INVALID_OPERATION` for focus or target loss), and is `null` for `Completed`.

`cancel_replay` does not wait for teardown. Its response is `Finalizing` while the owned PIE is still
ending (that end is a deferred engine request) or the terminal state if it already finished; a
`Finalizing` run reports no `waiting` or `current_frame`. Poll `get_run` until the state is terminal.

### Run evidence fields

A terminal `get_run` that reached the frame stage carries the evidence a validation verdict uses:

| Field | Meaning |
|---|---|
| `completed_frames` / `frame_count` | Recorded frames committed by this run / frames in the recording. Equal for `Completed`; a failed run keeps its partial frontier |
| `dispatched_events` / `total_events` | Recorded input events dispatched / events in the recording |
| `frames_sha256`, `inputs_sha256`, `initial_state_sha256`, `recording_snapshot_sha256` | Digests of the admitted recording files and snapshot (identity, not an observation of the run). Compare with `get_recording` to prove which recording ran |
| `behind_seconds` | Lag at the last paced frame (≥ 0); not a failure |
| `guard_coverage` | Press-only coverage fixed at capture |

A run is a faithful replay when it is `Completed` with `execution_error == null`, all frames and all
events, and the expected snapshot digest. Each committed frame ran with its recorded application
delta and world tick, otherwise the run would have ended `REPLAY_TIMEBASE_LOST`.

## Discovery, selection and paging

- Discovery returns only AI-enabled, complete recordings. Eligibility is checked before preparation
  and again before dispatch. Each row carries `duration_seconds` (recorded length, the sum of the
  recorded frame deltas) and `created_at_utc` (recording time).
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
  switching the editor's editing world), even when another map is open. It refuses with `EDITOR_BUSY`
  while unrelated PIE exists, so it never interrupts it, and never discards unsaved editor work.
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

For a pointer press on the shipped tagged-Slate route the guard also resolves the recorded tagged
widget identity and hit-tests the live pointer against it after preceding motion is processed.
Visibility, enabled state and hit-testability are required. A different widget is a mismatch; the
pointer is never relocated and the click is never retargeted. A press with no resolvable tagged-Slate
identity carries only the pose guard (partial coverage). Releases, cleanup releases and motion are not
gated, so press protection does not promise that a later OnClicked/OnReleased/drag action succeeded —
this press-only limit is surfaced in the recording popup, AI metadata and run results.

When a required UI target is missing, not yet ready, or its layout/input processing is pending, replay
may wait up to 1 second per press and at most 5 seconds cumulatively per run — only with neutral input
(no replay-owned key/button held, no active pointer capture or drag) and continued ownership, focus
and eligibility. Explicit readiness waits pause only the replay timeline: wait frames run on the
editor's own clock, the waited frame is committed without delta verification, and events are never
burst, skipped or compressed afterwards. There are no wall-clock deadlines to shift.

Replay is frame-locked: each recorded frame is one engine frame whose input is consumed by exactly
one world tick that runs with the recorded application delta, paced to wall time. During an owned
replay the editor runs on fixed application stepping (engine-wide, including editor UI timing) and
the human's fixed-step settings are restored at every terminal path. Admission refuses with
`INCOMPATIBLE_PREREQUISITES` when the editor is already in fixed-step, benchmarking or
fixed-frame-rate mode, a custom time step is installed or `t.OverrideFPS` is set — report it and ask
the human to leave that mode; do not change it yourself. `get_run` reports `behind_seconds` (≥ 0):
how far the recorded timeline trails wall-clock time **at the last paced frame**. It is live while
replaying and, on a terminal record, that same last value; it is not a maximum, because any unpaced
frame resets the lag. Being behind is not a failure. Slate "responsive mode" (dragging an editor
control) does not affect a run.

Capture records guard coverage as counts: `pose_presses`, `ui_supported_presses`,
`ui_unavailable_presses`, `ui_not_applicable_presses` (the response adds `guard_scope: "press_only"`).
A press whose reproducible widget identity cannot be obtained is marked `ui_guard_unavailable` and
keeps only its pose guard — that is explicit partial coverage, visible as a non-zero `ui_unavailable_presses` count. A previously
supported identity becoming unavailable at playback is an error, never an automatic downgrade.
Coverage is fixed by capture; AI permission does not upgrade it.

### UI identity: tagged runtime Slate only

The shipped capture/playback route supports exactly one UI guard identity: an authored unique root tag
plus an authored unique target tag on a runtime Slate control under the selected runtime root. Capture
resolves only that route and playback rejects any non-Slate / non-root-tag identity as unavailable.

| Target | Shipped status |
|---|---|
| Authored tagged runtime Slate pointer control under a uniquely identified selected runtime root | **Supported** — guarded |
| Untagged/anonymous Slate controls; type, caption or index alone | Unavailable — not an identity |
| Screen-space UMG/CommonUI authored ancestry | Unavailable — capture marks `ui_guard_unavailable` (`unobservable_pointer_route`); pose guard only |
| World-space Widget Component / saved-actor routes | Unavailable — same partial-coverage marking; no UI-target protection |

UMG/CommonUI and world-space Widget Component identity are **planned acceptance obligations for a
later release, not shipped behaviour** — never present them as available.

## Guard failure diagnostics

A guard failure finalizes the run `Error`, suppresses the blocked press and every later event, and
releases replay-owned held input exactly once. The error `code` identifies the failure family; there
is no uniform `sequence`/kind/guard-type envelope. `execution_error.details` is bounded and carries
only the fields listed per code:

- `REPLAY_POSE_GUARD_FAILED` — `position_delta_cm`, `pawn_rotation_delta_degrees`,
  `control_rotation_delta_degrees` and `max_scale_delta`, the measured deviation against the fixed
  tolerances. No event sequence or kind.
- `REPLAY_UI_GUARD_FAILED` — `reason` (`identity_mismatch`, `local_position_mismatch`,
  `unequivocal_mismatch`, `wait_not_permitted`, `missing_expected_selector`), `observation`,
  `tolerance`, `local_error`, `actual_x`, `actual_y`, plus `expected_identity_sha256` only when the
  guard recorded an expected selector. No event sequence or kind.
- `REPLAY_UI_WAIT_TIMEOUT` — no `details` object; the error message names the blocked event sequence.
- `REPLAY_TIMING_ERROR` — the replay clock produced an invalid (non-finite or backward) observation;
  `details` carries `sequence`. Lateness is not an error: a slow host falls behind (see
  `behind_seconds`) instead of failing. This is the only guard diagnostic that carries an event
  `sequence`, and it carries no kind.
- `REPLAY_TIMEBASE_LOST` — a replayed frame did not run with its recorded time step: another owner
  changed the engine clock, or the owned world did not tick as recorded (tick count, real delta or
  pause state).

Do not infer a missing `sequence`, kind or guard type from `waiting`, progress or coverage counters:
only `REPLAY_TIMING_ERROR` puts an event `sequence` in `details`, and the UI-wait-timeout message is
the only other place a blocked sequence appears.

Agents report drift with this evidence and ask the human to re-record; they do not retry, nudge,
change thresholds, teleport after time zero, or edit the recording.

## Preparation and environment errors

These codes are facts about the editor or machine, not gameplay verdicts. They appear as a synchronous
`start_replay` refusal or as the `execution_error` of the run (`Error`, or `Interrupted`/`Cancelled`
where noted). Report the code and message, take the action below, and never retry in a loop.

| Code | When | Meaning | Agent action |
|---|---|---|---|
| `EDITOR_BUSY` | Start refusal, or terminal `Error` | An unrelated PIE session, play request or pending teardown exists, or another capture/run owns the target | Ask the human to stop PIE or finish the other operation, then start again |
| `ASSET_NOT_FOUND` | Terminal `Error` | The recorded map package does not exist on this machine | Report; this recording cannot run here |
| `INPUT_PREPARATION_TIMEOUT` | Start refusal (snapshot validation) or terminal `Error` | The owned PIE target was not ready within the 30 s preparation deadline | Retry once if the editor was busy loading; otherwise report |
| `INPUT_POSE_MISMATCH` | Terminal `Error` | The recorded start pose read back differently after restoration | Report; ask the human to re-record on the current map/pawn |
| `INITIAL_POSE_RESTORE_FAILED` | Terminal `Error` | The recorded pawn class or pose could not be restored on the owned target | Report; ask the human to re-record on the current map/pawn |
| `INPUT_CLEANUP_FAILED` | Terminal `Error` | Releasing replay-held input failed, so cleanup is not claimed complete | Ask the human to check the editor's input state before another run |
| `INCOMPATIBLE_PREREQUISITES` | Start refusal, or terminal `Error` at readiness | Fixed-step timing, benchmarking, a fixed engine frame rate, a custom time step or `t.OverrideFPS` is active; or a recorded prerequisite differs: viewport size, DPI scale, input config (`player_input_class` / `input_config_sha256`), viewport mouse capture or high precision. `details.field`, `recorded` and `live` name a mismatch | Ask the human to remove the timing override or restore the viewport/input setup, or to re-record on this setup |
| `PERMISSION_DENIED` | Terminal `Error` when revoked before the epoch; `Cancelled` when revoked mid-run | The human withdrew AI permission, or the recording's metadata can no longer be read (for example it was deleted) | Stop; do not retry until the human re-enables the recording |
| `RECORDING_NOT_FOUND` | Start refusal only | No recording with that ID exists (an unloadable recording reports its own load error). A recording deleted after start surfaces as `PERMISSION_DENIED` | Run `list_recordings` again |
| `TARGET_UNAVAILABLE` | Terminal `Error` during preparation; `Interrupted` during replay | The owned PIE session, viewport or player was lost | Ask the human not to close PIE during a run, then start a new run |
| `REPLAY_INTERRUPTED_BY_INPUT` | Terminal `Interrupted` | Someone used the mouse or keyboard (foreign input) while the run was active. `execution_error.message` is a fixed title such as `Replay stopped: you moved the mouse`. `details` carry `cause: foreign_input`, `input_kind`, `input`, `edge` (press/release inputs only), `reason`, `stopped_at_frame`, `frame_count` and `stopped_at_seconds` | Report where it stopped. Retry once nobody is using the PC; do not loop. The editor also shows the human a toast with a Replay again button |

Focus loss and target loss do not use that code. They end the run `Interrupted` with the same fixed-title message and the same stop details (`reason`, `stopped_at_frame`, `frame_count`, `stopped_at_seconds`) under their own code: `INVALID_OPERATION` with `details.cause: focus_lost` (the game window lost focus; retry once nobody is using the PC and the game window keeps focus) or `INVALID_OPERATION` with `details.cause: target_lost` (treat it like `TARGET_UNAVAILABLE`).

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
    initial_state.json          # immutable player transform, view rotation and viewport mouse-capture/high-precision state
    inputs.jsonl.gz             # immutable ordered events and automatic guards (gzip of compact JSON Lines)
    frames.jsonl.gz             # immutable frame stream: one row per engine frame that consumed input after
                                #   the capture epoch (gzip of compact JSON Lines; row index = frame index)
<Project>/Saved/CortexReplay/
  Runs/                         # local per-run execution results and diagnostics
  Temp/                         # uncommitted capture/write scratch
```

Recordings are format 4: default-omitting rows in single-member gzip streams, at most 256 MiB per stream
(`LIMIT_EXCEEDED` on publish, `INVALID_RECORDING` on load). Format 1-3 recordings are refused
`UNSUPPORTED_RECORDING_FORMAT` and must be re-recorded. Payload hashes are checked before decompression
and parsing: a stream edited without updating its metadata hash is `INVALID_RECORDING`; with a matching hash it reaches row
validation (malformed row: `UNSUPPORTED_RECORDING_FORMAT`; a valid edit loads). Full contract:
`docs/systems/cortex-replay.md` in the UnrealCortex plugin project.

Recording files under `.cortex/replay/` are intended for Git tracking in the project (not the plugin
submodule); local runs, temp state and logs stay under `Saved/`. Replaying on another machine creates
a local result, never a dirty tracked recording. The payload hashes cover raw bytes, so the tracking
repository must not convert line endings: add `.cortex/replay/** -text` to the project's
`.gitattributes`, otherwise a checkout with Git's `autocrlf` setting enabled changes the payload bytes
and the recording fails its hash check on that machine. Legacy `Saved/CortexQA/Recordings/` and
`Saved/CortexQARecordings/` files are retained unchanged and are not valid physical-input recordings.
