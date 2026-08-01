"""Workflow files must be loadable by GitHub Actions, not merely valid YAML.

GitHub rejects a workflow containing duplicate keys: the run fails at startup
in 0s, with no job and no useful message, and — because the workflow never
starts — a pull_request check cannot report the problem either.

That is how a duplicate ``workflow_dispatch:`` reached main: two branches each
added the trigger at a different line, and git merged both without a conflict.
Every YAML check still passed, because a YAML parser is permitted to keep the
last of a duplicated key rather than reject it.

The scan below is deliberately dependency-free: this repository's Python is
stdlib-only and CI installs no packages, so importing PyYAML here would fail in
CI rather than catch anything. Workflow files are plain block mappings, which a
line scanner handles correctly.
"""

import unittest
from pathlib import Path

WORKFLOWS = Path(__file__).resolve().parent.parent / ".github" / "workflows"


def duplicate_keys(text: str) -> list[str]:
    """Return keys that appear twice in the same block mapping.

    Tracks one set of seen keys per indentation level, clearing deeper levels
    whenever indentation decreases, so ``jobs.a.runs-on`` and ``jobs.b.runs-on``
    are not mistaken for duplicates of each other.

    A ``- `` sequence item also starts a fresh mapping: every step in a job may
    legitimately carry its own ``with:`` and ``run:``.
    """
    seen: dict[int, set[str]] = {}
    found: list[str] = []
    for raw in text.splitlines():
        line = "" if raw.lstrip().startswith("#") else raw.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip())
        for level in [lv for lv in seen if lv > indent]:
            del seen[level]
        stripped = line.strip()
        if stripped.startswith("-"):
            # New sequence item: its mapping starts empty.
            for level in [lv for lv in seen if lv >= indent]:
                del seen[level]
            stripped = stripped[1:].strip()
            indent += 2
            if not stripped:
                continue
        key, sep, _ = stripped.partition(":")
        if not sep:
            continue
        bucket = seen.setdefault(indent, set())
        if key in bucket:
            found.append(key)
        bucket.add(key)
    return found


class WorkflowFileTests(unittest.TestCase):
    def test_workflow_directory_is_present(self):
        self.assertTrue(WORKFLOWS.is_dir(), f"missing {WORKFLOWS}")
        self.assertTrue(list(WORKFLOWS.glob("*.yml")), "no workflow files found")

    def test_workflows_have_no_duplicate_keys(self):
        for path in sorted(WORKFLOWS.glob("*.yml")):
            with self.subTest(workflow=path.name):
                dupes = duplicate_keys(path.read_text(encoding="utf-8"))
                self.assertEqual(
                    dupes, [],
                    f"{path.name} would be rejected by GitHub Actions: duplicate "
                    f"key(s) {dupes}. The run fails at startup in 0s with no job.",
                )

    def test_every_workflow_declares_a_name(self):
        """An unnamed workflow is displayed as its path, hiding what failed."""
        for path in sorted(WORKFLOWS.glob("*.yml")):
            with self.subTest(workflow=path.name):
                first = path.read_text(encoding="utf-8").splitlines()[0]
                self.assertTrue(
                    first.startswith("name:") and first[5:].strip(),
                    f"{path.name} has no top-level name on its first line",
                )

    def test_scanner_detects_a_duplicate(self):
        """Guards the guard: a scanner that never fires would protect nothing."""
        self.assertEqual(
            duplicate_keys("on:\n  push:\n  workflow_dispatch:\n  workflow_dispatch:\n"),
            ["workflow_dispatch"],
        )

    def test_scanner_allows_repeats_at_different_nesting(self):
        self.assertEqual(
            duplicate_keys("jobs:\n  a:\n    runs-on: x\n  b:\n    runs-on: y\n"), []
        )


if __name__ == "__main__":
    unittest.main()
