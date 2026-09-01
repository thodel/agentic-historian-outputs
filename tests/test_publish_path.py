"""End-to-end check of the publish path (#201).

Publishing a document must leave ``main`` green without manual intervention,
list the document in the catalogue, and produce the citable artifacts.

Why this test exists in this shape
----------------------------------

Twice now a change passed its pull_request check and then broke ``main``:

* #198 — generated pages embedded facts about the commit that created them.
  On a PR the merge base is already the PR's base commit, so the
  self-reference resolved harmlessly and the check went green.
* the duplicate ``workflow_dispatch`` key — two branches each added the
  trigger at a different line and git merged both without a conflict,
  producing a file neither branch contained.

Both were only observable where ``origin/main == HEAD``, which is the
push-to-main condition and is exactly what no pull_request build reproduces.
This test therefore clones the repository into a throwaway directory, pins
``origin/main`` to ``HEAD`` to recreate that condition, publishes a document,
and asserts the whole path.

It deliberately does **not** publish a fixture into the real ``docs/`` tree.
The public catalogue already carries eight test documents, which epic #184
exists to remove; verifying the publish path by adding a ninth would make the
problem worse to prove a point about it.

One caveat when running this locally: it clones the repository, so it exercises
the **committed** HEAD, not your working tree. Uncommitted changes to
``scripts/`` are invisible to it. In CI that is exactly right — the checkout is
the commit under test — but locally, commit before trusting a pass.
"""

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PROBE = "publish-path-probe"  # avoids "test", which the generators quarantine


def git(*args, cwd, check=True):
    return subprocess.run(
        ["git", *args], cwd=cwd, check=check, capture_output=True, text=True,
    )


def has_git_repo() -> bool:
    return (REPO / ".git").exists() and shutil.which("git") is not None


@unittest.skipUnless(has_git_repo(), "needs a git checkout")
class PublishPathTests(unittest.TestCase):
    """Publish a document into a clone and assert the whole path holds."""

    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.clone = Path(cls._tmp.name) / "repo"
        git("clone", "--quiet", str(REPO), str(cls.clone), cwd=REPO)
        git("config", "user.email", "t@example.com", cwd=cls.clone)
        git("config", "user.name", "Publish Path Test", cwd=cls.clone)
        # Recreate the push-to-main condition: on a push, origin/main IS HEAD.
        git("update-ref", "refs/remotes/origin/main", "HEAD", cwd=cls.clone)

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def build(self):
        result = subprocess.run(
            ["python3", "scripts/build_index.py"],
            cwd=self.clone, capture_output=True, text=True,
        )
        self.assertEqual(
            result.returncode, 0,
            f"build_index.py failed:\n{result.stdout}\n{result.stderr}",
        )

    def dirty_files(self):
        return [
            line[3:] for line in
            git("status", "--porcelain", cwd=self.clone).stdout.splitlines()
        ]

    def test_01_checkout_is_reproducible(self):
        """Rebuilding an untouched checkout must change nothing."""
        self.build()
        self.assertEqual(
            self.dirty_files(), [],
            "rebuilding a clean checkout dirtied it; the build is not "
            "reproducible and every publish will fail the clean-diff gate",
        )

    def test_02_publishing_generates_the_document(self):
        """Phase one: the publisher commits pipeline.json, the build renders it.

        A first publication legitimately dirties the tree — the publisher
        commits only ``pipeline.json`` and the generated page, TEI and citation
        do not exist yet. That is what the catalogue-index workflow's follow-up
        commit is for. The invariant that matters is asserted in phase two.
        """
        document = self.clone / "docs" / PROBE
        document.mkdir(parents=True, exist_ok=True)
        (document / "pipeline.json").write_text(json.dumps({
            "doc_id": PROBE,
            "transcription": "Probe-Transkription für den Publikationspfad.",
            "description": {
                "source_description": "Sondierung des Publikationspfads.",
                "source_json": {"Datierung": "1500", "Sprache": "Deutsch"},
            },
            "entities": [],
            "errors": [],
            "a_meta": {"transcription": "probe", "qa_score": 0.9},
            "recognitions": [],
        }, ensure_ascii=False, indent=2), encoding="utf-8")

        # A publish is a commit; on the push, origin/main advances with it.
        git("add", "-A", cwd=self.clone)
        git("commit", "-q", "-m", f"Publish {PROBE}", cwd=self.clone)
        git("update-ref", "refs/remotes/origin/main", "HEAD", cwd=self.clone)

        self.build()
        self.assertTrue(
            (document / "index.md").is_file(),
            "publishing a pipeline.json did not produce a document page",
        )

    def test_03_the_refresh_commit_settles(self):
        """Phase two: the invariant. After the refresh commit, main is clean.

        This is what "finishes green without manual intervention" means. The
        catalogue-index workflow commits the generated output as
        ``build: refresh catalogue index``; rebuilding at that commit must
        produce no further change. When it does not, main stays red — which is
        how the koenige breakage hid for seven days (#198), and what #208 fixed
        for a document's *first* publication.
        """
        git("add", "-A", cwd=self.clone)
        git("commit", "-q", "-m", "build: refresh catalogue index", cwd=self.clone)
        git("update-ref", "refs/remotes/origin/main", "HEAD", cwd=self.clone)

        self.build()
        self.assertEqual(
            self.dirty_files(), [],
            "the tree is still dirty after the refresh commit, so "
            "`git diff --exit-code` fails and main stays red (#198, #201)",
        )

    def test_04_document_reaches_the_catalogue(self):
        catalogue = (self.clone / "docs" / "index.md").read_text(encoding="utf-8")
        self.assertIn(
            f'data-document-id="{PROBE}"', catalogue,
            "published document is missing from the catalogue; it would be live "
            "but unreachable, as koenige was for seven days",
        )

    def test_05_citable_artifacts_are_generated(self):
        document = self.clone / "docs" / PROBE
        for artifact in ("index.md", "transcription.tei.xml", "CITATION.cff"):
            with self.subTest(artifact=artifact):
                self.assertTrue(
                    (document / artifact).is_file(), f"missing {artifact}",
                )

    def test_06_document_page_is_discoverable(self):
        page = (self.clone / "docs" / PROBE / "index.md").read_text(encoding="utf-8")
        self.assertIn("application/ld+json", page, "page carries no JSON-LD (#119)")
        self.assertIn(PROBE, page)

    def test_07_sitemap_lists_the_document(self):
        sitemap = (self.clone / "docs" / "sitemap.xml").read_text(encoding="utf-8")
        self.assertIn(f"/{PROBE}/", sitemap)


if __name__ == "__main__":
    unittest.main()
