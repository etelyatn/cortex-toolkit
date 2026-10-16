# PR #46 migration contract verification

## Candidate and endpoint

- Base/current remote main: `cc901ae0159f58813f4e48214ff55c86c8cb0bdc` (fetched before work; GitHub commits/main reconfirmed after checks).
- Candidate: local adaptation on toolkit branch `docs/pr46-migration-contract`; the task commit preserves the reviewed implementation and these records.
- Original PR head: `38bbecce62c8d58e115ce936dca1a5450921f1e1`; [PR #46](https://github.com/etelyatn/cortex-toolkit/pull/46) reconfirmed OPEN and draft, same head. Its base metadata still reports historical `f74ace387491a61a14dc8dfb05d1b2d87ebf5407`; that is not treated as current main.
- Endpoint: local commit only. No push, PR edit, merge, closure, editor launch, or asset mutation performed.

## Size and scope

| Skill measure | Before | After |
|---|---:|---:|
| Lines | 1338 | 239 |
| UTF-8 bytes | 74618 | 26869 |

One skill refactored in place; no relocated copy of the old narrative. Existing phase guides unchanged. One brittle phrase-matching test and its sole-use fixture removed, not replaced with new prose assertions. Design/implementation records added in `docs/plans/`.

## Reference-application smoke

Fresh, stateless model calls used the same four-case exercise with (1) no toolkit reference, (2) the original skill, (3) the adapted skill. No editor tools were available; this is simulated guidance usage, not native or MCP runtime validation.

| Case | Observed result with adapted skill |
|---|---|
| Audit + fast, unverified ticket class | Analysis/report only; no generation/execution; eligibility distinguished from tool proof; ticket treated as a lead; correct report path. |
| Approved fast migration | Exact Fast-1–Fast-14 actions and owners; numeric state IDs; per-task persistence; no routine extra verification/backup gate; failure inspects current state rather than re-executing migration. |
| Missing bounded prune and ambiguous apply | Required two-preview/second-token route; no raw cleanup/batch/Python fallback; explicit save authority; stop/readback reconciliation before another mutation. |
| Widget Everything possible and durable artifacts | Native semantic state/BP editable presentation; typed String Table metadata and save/reload; reference-aware required binding rename; owning-screen checks; all documented state keys/sections retrieved. |

The no-guidance control explicitly could not substantiate report paths, Fast task IDs or durable schema. The original-skill answer identified a real reference contradiction: its three-file maximum excludes its separately mandatory `migration-report.md`. The adapted answer enumerated all four allowed document artifacts without that contradiction.

Ephemeral session evidence: `local://pr46-reference-control.md`, `local://pr46-reference-before.md`, `local://pr46-reference-after.md`. These are session artifacts, not required repository files. This single exercise is not a statistical quality/cost benchmark, does not reproduce the contributor's A/B scores, and does not establish production migration correctness.

## Initial checks (before packaging correction)

All commands used the required rtk wrapper, from the toolkit repository.

| Check | Result |
|---|---|
| `rtk bash -lc 'bash tests/test-skill-taxonomy.sh'` | PASS as first command of the combined validation run. |
| `rtk bash -lc 'bash tests/test-opencode-plugin.sh'` | PASS as first command of the remaining-checks run. |
| `rtk bash -lc 'python3 -m unittest discover -s tests -p "test_*.py" -v'` | PASS: 29 tests, 0 failures/errors, 0.581 seconds. |
| `rtk bash -lc 'bash tests/test-codex-plugin.sh'` | FAIL: `Codex hooks must not call bash directly on Windows`. Existing baseline mismatch, not fixed here. |

Failure history: initial Python invocation used `python`, unavailable in the rtk-launched Bash environment; supported `python3` ran successfully. Initial 30-test suite had three subtest failures in one wording-only test because equivalent bounded-prune wording did not match exact phrases. The test plus now-unused phrase fixture was removed per project testing policy; remaining 29 tests pass. No functional or fixture-schema assertion was changed to hide failure.

Baseline proof for Codex check: `rtk git show cc901ae:hooks/hooks.json` contains `bash "${CLAUDE_PLUGIN_ROOT}/hooks/run-hook.cmd" ...` for both hooks, while `tests/test-codex-plugin.sh:106-107` rejects a command starting with `bash `. History identifies `f46f467` as the hook change. Both files are untouched by this adaptation. Overall packaging is therefore not all-green; publication/integration readiness is not claimed.

## Independent reviews

Two read-only reviewers separately compared the candidate with the original skill and existing resources:

- Durable state, resume, full/fast tasks, approval gates and phase handoffs: no substantive findings.
- Widget/Blueprint ownership, localization, guarded graph/save boundaries, evidence and attribution: no substantive findings.
- The state reviewer also reviewed the final prose-test deletion: confirmed no executable behavior, schema validation, or functional test coverage was removed; no substantive finding.

Reviewers ran no tests or asset operations. Acceptance evidence above was exercised by the controller. No new public skill, native command, module architecture, or project convention was introduced, so no additional help catalog/system-reference sync is required.

## Workspace

The toolkit was clean on main at intake and equal to freshly fetched origin/main. The task-owned branch retains the local adaptation for inspection. Parent pre-existing skill/config/schema modifications and modified plugin/toolkit gitlinks were not staged, reverted, or committed. No cleanup requiring reset, force deletion or stash was performed.

## Continuation verification

On the user's request to review the design if necessary and then execute the plan, the existing two independent reviews and implemented candidate were reconciled before taking action. No outstanding findings or unimplemented in-scope steps were identified; the implementation guide now records that status explicitly.

Fresh command against the same local candidate:

```bash
rtk bash -lc 'bash tests/test-skill-taxonomy.sh && bash tests/test-opencode-plugin.sh && python3 -m unittest discover -s tests -p "test_*.py" -v'
```

Result: taxonomy PASS, OpenCode packaging PASS, 29 Python tests PASS (0 failures/errors, 0.869 seconds). The previously established Codex failure was not rerun merely to reconfirm it and remains an explicit full-packaging acceptance gap. Only these status/evidence records changed during continuation; no skill, production code, test behavior, asset or remote state was changed.

## Packaging blocker resolution

The next user continuation covered resolving the remaining validation mismatch. The only additional code change is deletion of the obsolete two-line `startswith("bash ")` prohibition in `tests/test-codex-plugin.sh`. Remaining hook presence/matcher/wrapper/script checks are unchanged. Production hook scripts, manifest, permissions and opt-in behavior are untouched.

### Actual configured-command smoke

The controller read commands from `hooks/hooks.json`, copied the actual hook files into disposable fixtures whose plugin/project paths contained spaces, then executed the configured commands:

| Environment | Default-off SessionStart and PreToolUse | Enabled SessionStart |
|---|---|---|
| Native Windows Git Bash, using the Windows worktree bytes | Both exit 0, empty stdout/stderr. | Exit 0, exact fixture context emitted. |
| POSIX `/bin/sh`/Bash, LF deployment fixture with wrapper mode 0644 | Both exit 0, empty stdout/stderr; no project files created. | Exit 0, exact fixture context emitted through the non-executable wrapper. |

In the POSIX fixture, the historical direct-wrapper command without the `bash` prefix exits 126 with `Permission denied`; the current manifest command succeeds. This independently supports the already-shipped `f46f467` change rather than merely trusting its commit message.

Environment finding: the Windows checkout has `core.autocrlf=true` and CRLF worktree hook files, while index blobs are LF. Copying raw Windows bytes into a POSIX fixture first failed on CRLF commands; the POSIX fixture was corrected to use LF deployment content. Native Windows smoke passed with the actual Windows worktree bytes. No repository line-ending policy or runtime code was changed to accommodate the fixture.

### Validation and review

After the deletion, Codex packaging, taxonomy and OpenCode packaging checks pass. A broader attempt through the WSL-backed `rtk bash` reached the unchanged CRLF `test-hook-optin.sh` and failed with `set: pipefail ... invalid option name`; this is an interpreter/checkout mismatch, not a green suite. The supported native Windows Git Bash invocation is used for the broader hook suite.

The existing state reviewer independently reviewed this final delta and reported no substantive finding: no production behavior or functional execution test was removed, and manifest/wrapper routing assertions remain.

### Final supported-environment suite

```bash
rtk proxy "C:/Program Files/Git/bin/bash.exe" -lc 'bash tests/test-codex-plugin.sh && bash tests/test-skill-taxonomy.sh && bash tests/test-opencode-plugin.sh && bash tests/test-hook-optin.sh && bash tests/test-opencode-hooks.sh && bash tests/test-check-ue-editor-config.sh && bash tests/test-config-loader.sh && python -m unittest discover -s tests -p "test_*.py" -v'
```

Result: all seven shell suites PASS; all 29 Python tests PASS (0 failures/errors, 0.032 seconds). The combined command completed successfully in 197.31 seconds. This resolves the previously recorded Codex packaging gap; no test was re-pinned to a new command string and no production hook behavior changed.

The final reviewed local delta therefore includes the migration skill refactor, obsolete validation removals in the two test files, and its design/implementation/verification records, preserved on `docs/pr46-migration-contract`. No push, remote PR mutation, merge, parent gitlink commit, editor restart or user-asset change was performed.
