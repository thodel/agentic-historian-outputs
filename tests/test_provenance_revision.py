"""Generated output must be a pure function of the committed tree (#198, #201).

A document page records its own version history and dates.  Those facts are
read from the document's *input* (``docs/<id>/pipeline.json``), so the question
"which commits touched this document" must have the same answer at every
revision from the publishing commit onwards.  When it does not, the page
rewrites itself on a later build and ``git diff --exit-code`` turns ``main``
red.

Two shapes of that bug have now been seen:

* #198/#201 — reading at HEAD while deriving facts from the *generated page*,
  so a page described the commit that created it.
* the sliding window — reading at ``HEAD^``/``HEAD^^`` to dodge the first
  shape.  That stabilised the publishing commit and destabilised every other
  one: the first unrelated commit pushed after a publication re-dated the
  document.  The test that caught #201 stopped at the refresh commit, so it
  never looked one commit further.

The tests below therefore assert stability across the refresh commit *and*
across the unrelated commits that follow it.  They build throwaway
repositories and reproduce the push-to-main condition, which no pull_request
build reproduces.
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

    def _in_repo(self, call):
        """Run *call* with the throwaway repo as the working directory."""
        import os
        previous = os.getcwd()
        os.chdir(self.repo)
        try:
            return call()
        finally:
            os.chdir(previous)

    def _revision_in_repo(self):
        return self._in_repo(build_outputs.provenance_revision)

    def _history_of(self, relative="pipeline.json"):
        """Resolve the document's history exactly as the generators do."""
        return self._in_repo(lambda: build_outputs.git_history(Path(relative)))

    # ── the revision policy ──────────────────────────────────────────────

    def test_revision_is_head(self):
        """Facts come from the input file, so HEAD is the correct revision.

        Anything expressed as a distance from HEAD slides with HEAD and
        re-dates published documents on unrelated pushes.
        """
        head = self._commit("first", '{"doc_id": "a"}')
        self.assertEqual(
            git("rev-parse", self._revision_in_repo(), cwd=self.repo), head,
        )

    def test_revision_resolves_in_a_single_commit_repository(self):
        """There is no parent to fall back to; HEAD must still resolve."""
        head = self._commit("only commit", '{"doc_id": "a"}')
        self.assertEqual(
            git("rev-parse", self._revision_in_repo(), cwd=self.repo), head,
        )

    # ── the invariant that keeps main green ──────────────────────────────

    def test_history_is_stable_across_the_refresh_commit(self):
        """Publishing, then committing the generated page, must not move it."""
        self._commit("unrelated site baseline", "x = 1\n", name="tool.py")
        self._commit("Publish new document", '{"doc_id": "new"}')
        at_publish = self._history_of()

        self._commit("build: refresh catalogue index", "generated\n",
                     name="index.md")
        self.assertEqual(
            at_publish, self._history_of(),
            "the refresh commit changed the document's resolved history, so "
            "the page it just committed is already stale (#201)",
        )

    def test_history_is_stable_across_later_unrelated_commits(self):
        """The regression the old HEAD^ policy allowed through.

        After a publication has settled, ordinary site and tooling commits
        must leave every published document's provenance untouched.  Under the
        sliding window the first such commit re-dated the document and the
        clean-diff gate failed on a push nobody connected to publishing.
        """
        self._commit("unrelated site baseline", "x = 1\n", name="tool.py")
        self._commit("Publish new document", '{"doc_id": "new"}')
        self._commit("build: refresh catalogue index", "generated\n",
                     name="index.md")
        settled = self._history_of()

        for number in range(1, 4):
            self._commit(f"chore: unrelated change {number}",
                         f"x = {number + 100}\n", name="tool.py")
            self.assertEqual(
                settled, self._history_of(),
                f"unrelated commit {number} moved a published document's "
                "history; the next build dirties the page and main goes red",
            )

    def test_publication_is_visible_immediately(self):
        """A published document shows the commit that published it.

        The old policy hid it until some later commit happened to slide the
        window forward, which is how the same page could report two different
        creation dates over its life.
        """
        self._commit("unrelated site baseline", "x = 1\n", name="tool.py")
        head = self._commit("Publish new document", '{"doc_id": "new"}')

        history = self._history_of()
        self.assertEqual(
            [entry[0] for entry in history], [head[:len(history[0][0])]],
            "a freshly published document must report its publishing commit",
        )

    def test_history_grows_only_when_the_document_changes(self):
        """A republish adds exactly one entry, and then settles again."""
        self._commit("unrelated site baseline", "x = 1\n", name="tool.py")
        self._commit("Publish document", '{"doc_id": "a"}')
        self._commit("build: refresh catalogue index", "generated\n",
                     name="index.md")
        first = self._history_of()

        self._commit("chore: unrelated", "x = 2\n", name="tool.py")
        self.assertEqual(first, self._history_of())

        self._commit("Publish document", '{"doc_id": "a", "n": 2}')
        republished = self._history_of()
        self.assertEqual(
            len(first) + 1, len(republished),
            "republishing must add exactly one history entry",
        )

        self._commit("chore: unrelated again", "x = 3\n", name="tool.py")
        self.assertEqual(
            republished, self._history_of(),
            "the republished document did not settle",
        )


class ShallowCloneTests(unittest.TestCase):
    """A truncated history yields wrong provenance, not missing provenance.

    Git reports a shallow clone's boundary commit as having introduced every
    file it can still see, so the build succeeds and publishes fiction.  It
    must refuse instead.
    """

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def _in(self, path, call):
        import os
        previous = os.getcwd()
        os.chdir(path)
        try:
            return call()
        finally:
            os.chdir(previous)

    def test_full_clone_is_accepted(self):
        origin = self.root / "origin"
        origin.mkdir()
        git("init", "-q", "-b", "main", cwd=origin)
        git("config", "user.email", "t@example.com", cwd=origin)
        git("config", "user.name", "Test", cwd=origin)
        for number in range(3):
            (origin / "f.txt").write_text(f"{number}\n", encoding="utf-8")
            git("add", "-A", cwd=origin)
            git("commit", "-q", "-m", f"c{number}", cwd=origin)

        self._in(origin, build_outputs.assert_complete_history)  # must not raise

    def test_shallow_clone_is_refused(self):
        origin = self.root / "origin"
        origin.mkdir()
        git("init", "-q", "-b", "main", cwd=origin)
        git("config", "user.email", "t@example.com", cwd=origin)
        git("config", "user.name", "Test", cwd=origin)
        for number in range(3):
            (origin / "f.txt").write_text(f"{number}\n", encoding="utf-8")
            git("add", "-A", cwd=origin)
            git("commit", "-q", "-m", f"c{number}", cwd=origin)

        shallow = self.root / "shallow"
        git("clone", "-q", "--depth", "1", f"file://{origin}", str(shallow),
            cwd=self.root)

        with self.assertRaises(SystemExit) as caught:
            self._in(shallow, build_outputs.assert_complete_history)
        self.assertIn("shallow", str(caught.exception).lower())


if __name__ == "__main__":
    unittest.main()
