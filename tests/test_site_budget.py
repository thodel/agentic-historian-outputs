"""What the generated site weighs, and what a corpus would do to it (#239).

Per-run and per-page budgets existed; the site as a whole had none, so
nothing would notice a corpus import until GitHub Pages did. The numbers that
matter are per document, because those are what a corpus multiplies: a single
document page was 325 KB of generated markup, which is unremarkable eight
times and 650 MB two thousand times.

The report exits non-zero over budget rather than raising during generation.
A budget that aborts the build cannot be acted on, only obeyed — the cliff
that made a long training run a publication blocker (#227).
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from site_budget import (  # noqa: E402
    SITE_BUDGETS, measure, projection, report_text, violations,
)

ROOT = Path(__file__).parent.parent


class MeasurementTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.docs = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def _document(self, doc_id, page_bytes=1000):
        directory = self.docs / doc_id
        directory.mkdir(parents=True)
        (directory / "pipeline.json").write_text(
            json.dumps({"doc_id": doc_id}), encoding="utf-8")
        (directory / "index.md").write_text("x" * page_bytes, encoding="utf-8")

    def test_documents_are_grouped_together(self):
        self._document("a")
        self._document("b")
        report = measure(self.docs)
        self.assertEqual(2, report["documents"])
        self.assertIn("documents/", report["areas"])

    def test_entities_and_assets_are_separate_areas(self):
        self._document("a")
        for area in ("entities", "assets"):
            (self.docs / area / "x").mkdir(parents=True)
            (self.docs / area / "x" / "index.md").write_text("y" * 50, encoding="utf-8")
        report = measure(self.docs)
        self.assertIn("entities/", report["areas"])
        self.assertIn("assets/", report["areas"])

    def test_standalone_pages_do_not_each_become_their_own_area(self):
        """A dozen 947-byte tombstones buried the numbers that matter."""
        self._document("a")
        for name in ("tombstone-one", "tombstone-two", "tombstone-three"):
            (self.docs / name).mkdir()
            (self.docs / name / "index.md").write_text("z" * 40, encoding="utf-8")
        report = measure(self.docs)
        self.assertEqual(
            [], [area for area in report["areas"] if "tombstone" in area],
            "each standalone page became its own area row",
        )
        self.assertIn("other pages/", report["areas"])
        self.assertEqual(3, report["area_counts"]["other pages/"])

    def test_build_artifacts_are_not_counted(self):
        """Jekyll's cache is local, never published, and dwarfs the site."""
        self._document("a")
        cache = self.docs / ".jekyll-cache" / "Jekyll"
        cache.mkdir(parents=True)
        (cache / "blob").write_text("q" * 100_000, encoding="utf-8")
        report = measure(self.docs)
        self.assertLess(report["total_bytes"], 50_000)

    def test_the_largest_files_are_named(self):
        self._document("small", page_bytes=100)
        self._document("large", page_bytes=9000)
        report = measure(self.docs)
        self.assertIn("large/index.md", report["largest_files"][0][1])


class BudgetTests(unittest.TestCase):
    def _report(self, total, pages):
        return {"total_bytes": total, "page_sizes": pages, "documents": len(pages),
                "per_document": pages, "mean_document_bytes": 0,
                "mean_page_bytes": 0, "areas": {}, "area_counts": {},
                "largest_files": []}

    def test_a_site_within_budget_reports_nothing(self):
        self.assertEqual([], violations(self._report(1000, {"a": 100})))

    def test_an_oversized_site_is_reported(self):
        report = self._report(SITE_BUDGETS["total_bytes"] + 1, {"a": 100})
        self.assertTrue(any("generated site" in problem for problem in violations(report)))

    def test_an_oversized_document_page_is_named(self):
        page = SITE_BUDGETS["document_page_bytes"] + 1
        problems = violations(self._report(1000, {"heavy": page}))
        self.assertTrue(any("heavy" in problem for problem in problems))

    def test_oversized_pages_are_reported_worst_first(self):
        budget = SITE_BUDGETS["document_page_bytes"]
        problems = violations(self._report(1000, {"a": budget + 10, "b": budget + 99}))
        self.assertIn("b", problems[0])


class ProjectionTests(unittest.TestCase):
    def test_the_projection_is_declared_a_floor(self):
        """It scales documents only; entity pages grow with the corpus too."""
        report = {"total_bytes": 10_000, "per_document": {"a": 5_000},
                  "mean_document_bytes": 5_000, "mean_page_bytes": 3_000}
        text = projection(report, documents=100)
        self.assertIn("at least", text)
        self.assertIn("floor", text)

    def test_an_empty_corpus_projects_nothing(self):
        report = {"total_bytes": 0, "per_document": {},
                  "mean_document_bytes": 0, "mean_page_bytes": 0}
        self.assertIn("nothing to project", projection(report))

    def test_a_corpus_over_budget_says_so(self):
        report = {"total_bytes": 10_000, "per_document": {"a": 10_000},
                  "mean_document_bytes": 10_000, "mean_page_bytes": 9_000}
        self.assertIn("OVER", projection(report, documents=1_000_000))


class LiveSiteTests(unittest.TestCase):
    """The published site must stay inside its own budget."""

    def test_the_committed_site_is_within_budget(self):
        report = measure(ROOT / "docs")
        problems = violations(report)
        self.assertEqual(
            [], problems,
            "the published site is over budget:\n  " + "\n  ".join(problems),
        )

    def test_the_report_names_its_largest_contributors(self):
        text = report_text(measure(ROOT / "docs"))
        self.assertIn("Largest single files:", text)
        # "documents/" is an area of the report, so it appears when documents
        # do. Every output is withdrawn (#254); the report then has to say so
        # rather than silently omitting the projection the budget exists for.
        if any((ROOT / "docs").glob("*/pipeline.json")):
            self.assertIn("documents/", text)
        else:
            self.assertIn("No documents published", text)


if __name__ == "__main__":
    unittest.main()
