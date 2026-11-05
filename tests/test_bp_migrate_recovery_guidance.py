"""Guard the recovery invariants of the cortex-bp-migrate pipeline (#74 slow review).

The skill is prose, so these checks pin the load-bearing rules an agent must follow: resident packages
are reloaded after every restore, each package is restored from its recorded baseline (not HEAD), the
dependent write set is complete before a saving rename, and a VERIFY crash is reconciled by readback.
"""

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL = (ROOT / "skills" / "cortex-bp-migrate" / "SKILL.md").read_text(encoding="utf-8")
FINALIZER = (ROOT / "resources" / "bp-migration-finalizer.md").read_text(encoding="utf-8")
EXECUTOR = (ROOT / "resources" / "bp-migration-executor.md").read_text(encoding="utf-8")


def section(text: str, start: str, end: str) -> str:
    begin = text.index(start)
    return text[begin:text.index(end, begin)]


ROLLBACK = section(SKILL, "**Rollback** (abort", "## Phase Writes")
WRITE_SET = section(SKILL, "**Dependent write set", "**Measured persistence")


class BpMigrateRecoveryGuidance(unittest.TestCase):
    def test_rollback_reloads_resident_packages_after_every_restore(self) -> None:
        reload_step = re.search(r"^\d+\. \*\*Reload the resident package, in every case\*\*.*$", ROLLBACK, re.M)
        self.assertIsNotNone(reload_step, "reload must be its own step, outside the git/copy restore branches")
        text = reload_step.group(0)
        for token in ("reload_asset", "reloaded: true", "every case", "git or Perforce restore", "each dependent"):
            self.assertIn(token, text)
        restore_step = section(ROLLBACK, "1. **Restore the bytes**", "2. **Reload")
        self.assertNotIn("reload_asset", restore_step.replace("no reload is needed", ""))
        verify = section(ROLLBACK, "3. **Verify disk and memory.**", "4. Abort")
        for token in ("package_saved_hash", "baseline_hash", "analyze_for_migration", "list_scs_components"):
            self.assertIn(token, verify)

    def test_restore_uses_the_recorded_baseline_not_head(self) -> None:
        for token in ("restore_source", "original_copy", "baseline_hash"):
            self.assertIn(token, ROLLBACK)
        self.assertIn("HEAD is never assumed to be the baseline", SKILL)
        git_line = next(line for line in ROLLBACK.splitlines() if "`restore_source: git`" in line)
        self.assertIn("git restore --source <git_commit_before>", git_line)
        self.assertNotIn("when the project uses Git", ROLLBACK)
        self.assertIn("restore_source", FINALIZER)
        self.assertIn("never", FINALIZER)
        self.assertIn("baseline_hash", FINALIZER)

    def test_dependent_write_set_is_complete_before_the_saving_rename(self) -> None:
        for token in ("total_unfiltered", "larger `limit`", "stop", "before the first `rename_scs_component`"):
            self.assertIn(token, WRITE_SET + SKILL[SKILL.index("**Dependent write set"):][:120])
        self.assertLess(WRITE_SET.index("complete referencer inventory"), WRITE_SET.index("copy its `.uasset`"))
        self.assertIn("Write `touched_dependents` to the frontmatter, then issue the rename", WRITE_SET)
        self.assertNotIn("after the call, add any dependent", SKILL)
        self.assertIn("total_unfiltered", EXECUTOR)

    def test_verify_crash_is_reconciled_by_readback(self) -> None:
        recovery = section(SKILL, "3. **Re-verify asset state before resuming**", "4. Resume from `failed_task`")
        self.assertNotIn("VERIFY is read-only", recovery)
        verify_line = next(line for line in recovery.splitlines() if "crash during EXECUTE or VERIFY" in line)
        for token in ("analyze_for_migration", "first EXECUTE task whose postcondition is unsatisfied"):
            self.assertIn(token, verify_line)


if __name__ == "__main__":
    unittest.main()
