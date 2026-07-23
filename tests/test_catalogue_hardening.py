import html
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from build_index import _card, _record, recognition_summary


class CatalogueHardeningTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = json.loads(
            (ROOT / "tests/fixtures/catalogue_cases.json").read_text(encoding="utf-8")
        )

    def test_fixture_matrix_covers_summary_contract_and_output_kinds(self):
        names = {case["name"] for case in self.cases}
        self.assertEqual(names, {
            "multi-engine-comparison-ready", "failed-attempt", "degenerate-attempt",
            "direct-image-source", "missing-source", "legacy-output", "test-output",
            "human-reviewed", "pipeline-ok-recognition-errors",
        })
        with tempfile.TemporaryDirectory() as temp:
            for case in self.cases:
                with self.subTest(case=case["name"]):
                    summary = recognition_summary(case["data"])
                    target = Path(temp) / case["document_id"] / "pipeline.json"
                    target.parent.mkdir(parents=True)
                    target.write_text(json.dumps(case["data"]), encoding="utf-8")
                    record = _record(target)
                    for key, expected in case["expected"].items():
                        if key == "is_test":
                            actual = record.is_test
                        else:
                            actual = getattr(summary, key)
                            if isinstance(actual, tuple):
                                actual = list(actual)
                        self.assertEqual(actual, expected)

    def test_cards_keep_summary_actions_and_accessible_disclosures_in_sync(self):
        with tempfile.TemporaryDirectory() as temp:
            for case in self.cases:
                with self.subTest(case=case["name"]):
                    target = Path(temp) / case["document_id"] / "pipeline.json"
                    target.parent.mkdir(parents=True)
                    target.write_text(json.dumps(case["data"]), encoding="utf-8")
                    record = _record(target)
                    markup = _card(record)
                    summary = record.recognition_summary
                    self.assertIn(f'data-recognition-total="{summary.total if summary.total is not None else ""}"', markup)
                    controls = re.findall(r'aria-controls="([^"]+)"', markup)
                    ids = set(re.findall(r'\bid="([^"]+)"', markup))
                    # aria-controls / explanation button should only be present
                    # when CER or WER is available on this record (issue #114).
                    has_cer_wer = (
                        record.reference_cer is not None
                        or record.reference_wer is not None
                    )
                    if has_cer_wer:
                        self.assertTrue(
                            controls,
                            "Card with CER/WER must contain aria-controls",
                        )
                    else:
                        self.assertFalse(
                            controls,
                            "Card without CER/WER must not emit aria-controls",
                        )
                    if controls:
                        self.assertTrue(set(controls).issubset(ids), (controls, ids))
                    action = re.search(r'class="catalogue-actions"><a href="([^"]+)"', markup)
                    self.assertIsNotNone(action)
                    href = html.unescape(action.group(1))
                    if summary.comparison_ready:
                        self.assertIn("?cmp=", href)
                        self.assertTrue(href.endswith("#recognitions"))
                    elif summary.total:
                        self.assertIn("?rec=selected#recognition-selected", href)
                    else:
                        self.assertNotIn("?", href)

    def test_every_generated_card_action_resolves_to_a_document_state(self):
        catalogue = (ROOT / "docs/index.md").read_text(encoding="utf-8")
        articles = re.findall(r'<article class="catalogue-card".*?</article>', catalogue, re.S)
        self.assertTrue(articles)
        for article in articles:
            document_id = re.search(r'data-document-id="([^"]+)"', article).group(1)
            action = re.search(r'class="catalogue-actions"><a href="([^"]+)"', article).group(1)
            url = urlsplit(html.unescape(action))
            target = ROOT / "docs" / url.path / "index.md"
            with self.subTest(document=document_id, action=action):
                self.assertTrue(target.is_file(), target)
                page = target.read_text(encoding="utf-8")
                if url.fragment:
                    self.assertIn(f'id="{url.fragment}"', page)
                query = parse_qs(url.query)
                if "rec" in query:
                    self.assertIn(f'data-recognition-panel="{query["rec"][0]}"', page)
                if "cmp" in query:
                    candidates = query["cmp"][0].split(":")
                    self.assertEqual(len(candidates), 2)
                    for candidate in candidates:
                        self.assertIn(f'data-recognition-panel="{candidate}"', page)

    def test_catalogue_markup_and_styles_cover_non_visual_and_responsive_states(self):
        catalogue = (ROOT / "docs/index.md").read_text(encoding="utf-8")
        css = (ROOT / "docs/assets/catalogue.css").read_text(encoding="utf-8")
        for control in ("search", "filter", "language", "script", "engine", "readiness", "failure", "source", "sort"):
            self.assertRegex(catalogue, rf'<label for="catalogue-{control}">[^<]+</label>')
        self.assertIn('id="catalogue-empty"', catalogue)
        self.assertIn("<noscript>", catalogue)
        self.assertIn("@media (max-width: 38rem)", css)
        self.assertIn("@media (prefers-contrast: more)", css)
        self.assertIn("@media (prefers-reduced-motion: no-preference)", css)
        self.assertIn(":focus-visible", css)
        self.assertIn("min-height: 2.75rem", css)


    def test_pipeline_badge_is_scoped_when_recognition_errors_present(self):
        """Issue #120: a card must not show an unscoped 'Ohne Fehler' badge
        alongside a recognition-error badge — that would be contradictory.
        The pipeline badge must carry the 'Pipeline:' scope prefix."""
        # Find the bat-like fixture: no pipeline errors but recognition failures
        case = next(c for c in self.cases if c["name"] == "pipeline-ok-recognition-errors")
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / case["document_id"] / "pipeline.json"
            target.parent.mkdir(parents=True)
            target.write_text(json.dumps(case["data"]), encoding="utf-8")
            record = _record(target)
            markup = _card(record)
            # Must show scoped pipeline badge
            self.assertIn("Pipeline: Ohne Fehler", markup,
                          "Pipeline-OK badge must carry 'Pipeline:' scope prefix")
            # Must NOT show bare unscoped 'Ohne Fehler' badge
            self.assertNotIn(">Ohne Fehler<", markup,
                             "Bare unscoped 'Ohne Fehler' badge must not appear")
            # Recognition errors badge must still be present
            self.assertIn("Erkennungsfehler", markup,
                          "Recognition-error badge must appear alongside scoped pipeline badge")


if __name__ == "__main__":
    unittest.main()
