"""Generated output must not describe the commit that creates it (#198).

A document page records its own version history and dates. Reading those at
HEAD makes the page describe the publishing commit, which cannot be committed
correctly — the page is stale the moment it lands and ``git diff --exit-code``
fails on the push.

The regression test below builds a throwaway repository and reproduces the
condition that actually breaks: a push to ``main``, where ``origin/main`` and
``HEAD`` are the same commit. That condition is invisible to a pull_request
build, whose merge base is already the PR's base commit, which is why this bug
survived several green PR checks before it was caught.
"""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import build_outputs  # noqa: E402


def git(*args, cwd):
    return subprocess.run(
        ["git", *args], cwd=cwd, check=True, capture_output=True, text=True,
    ).stdout.strip()


class ProvenanceRevisionTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self._tmp.name)
        git("init", "-q", "-b", "main", cwd=self.repo)
        git("config", "user.email", "t@example.com", cwd=self.repo)
        git("config", "user.name", "Test", cwd=self.repo)
        self.addCleanup(self._tmp.cleanup)

    def _commit(self, message, text, name="pipeline.json"):
        target = self.repo / name
        target.write_text(text, encoding="utf-8")
        git("add", "-A", cwd=self.repo)
        git("commit", "-q", "-m", message, cwd=self.repo)
        return git("rev-parse", "HEAD", cwd=self.repo)

    def _revision_in_repo(self):
        """Run provenance_revision() with the throwaway repo as cwd."""
        import os
        previous = os.getcwd()
        os.chdir(self.repo)
        try:
            return build_outputs.provenance_revision()
        finally:
            os.chdir(previous)

    def test_single_commit_repository_has_no_parent(self):
        """HEAD^ does not exist yet, so HEAD itself must be used."""
        head = self._commit("first", '{"doc_id": "a"}')
        self.assertEqual(
            git("rev-parse", self._revision_in_repo(), cwd=self.repo), head,
        )

    def test_resolves_one_commit_back(self):
        """With history present, the publishing commit is excluded."""
        first = self._commit("first", '{"doc_id": "a"}')
        self._commit("publish", '{"doc_id": "a", "changed": true}')
        self.assertEqual(
            git("rev-parse", self._revision_in_repo(), cwd=self.repo), first,
        )

    def _history_of(self, relative):
        """Resolve the document's history exactly as the generators do."""
        import os
        previous = os.getcwd()
        os.chdir(self.repo)
        try:
            return build_outputs.git_history(Path(relative))
        finally:
            os.chdir(previous)

    def test_document_history_is_unchanged_by_the_publishing_commit(self):
        """The property that actually keeps generated pages stable.

        Note this is about the *resolved history for a document*, not about the
        revision itself: the revision necessarily advances with every commit.
        What must not move is the answer to "which commits touched this
        document", evaluated before a publish and again after it — the latter
        being the push-to-main condition.

        It holds because the publishing commit is excluded, and the commit
        before it did not touch this document — which is the shape of a real
        publish, where the preceding commit is unrelated site or tooling work.
        """
        self._commit("publish document", '{"doc_id": "a"}')
        self._commit("unrelated tooling change", "x = 1\n", name="tool.py")
        before = self._history_of("pipeline.json")
        self._commit("republish document", '{"doc_id": "a", "n": 2}')
        after = self._history_of("pipeline.json")
        self.assertEqual(
            before, after,
            "the document's resolved history moved when it was published; "
            "generated pages will dirty themselves on the next build (#198)",
        )


if __name__ == "__main__":
    unittest.main()
