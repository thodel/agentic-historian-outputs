import sys
import tempfile
import unittest
from html.parser import HTMLParser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from build_recognitions import (
    _candidates,
    _confidence,
    _public_error,
    _recognition_path,
    _safe_slug,
    build_recognition_section,
)


class DOM(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.links = []
        self.panels = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get("id"):
            self.ids.append(attrs["id"])
        if tag == "a" and attrs.get("href"):
            self.links.append(attrs["href"])
        if attrs.get("data-recognition-panel"):
            self.panels.append(attrs)


def rec(engine="vlm", model="model", text="text", **extra):
    return {"engine": engine, "model_id": model, "text": text, **extra}


class RecognitionContractTests(unittest.TestCase):
    def test_empty_list_omits_section(self):
        self.assertEqual(build_recognition_section([], "doc", "text"), "")

    def test_selected_output_is_first(self):
        candidates = _candidates([rec()], "fused text")
        self.assertEqual(candidates[0]["id"], "selected")
        self.assertEqual(candidates[0]["text"], "fused text")

    def test_duplicate_ids_are_unique(self):
        candidates = _candidates([rec(), rec()], "fused")
        ids = [c["id"] for c in candidates]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(candidates[1]["path"], "")
        self.assertEqual(candidates[2]["path"], "")

    def test_ids_are_sanitized(self):
        value = _safe_slug('Kraken <script> " model/id')
        self.assertRegex(value, r"^[a-z0-9-]+$")

    def test_page_aware_publisher_path(self):
        candidate = rec("kraken", "10.5281/zenodo.1", page="Page 1.jpg")
        self.assertEqual(
            _recognition_path(candidate),
            "recognitions/Page_1/kraken-10.5281_zenodo.1.txt",
        )

    def test_confidence_is_typed_and_clamped(self):
        self.assertEqual(_confidence(.82), "82%")
        self.assertEqual(_confidence(7), "100%")
        self.assertEqual(_confidence(None), "Nicht angegeben")

    def test_error_messages_hide_internal_details(self):
        raw = "Kraken service error at http://10.0.0.8:8200/ocr: timed out token=secret"
        public = _public_error(raw)
        self.assertIn("Zeitlimit", public)
        self.assertNotIn("10.0.0.8", public)
        self.assertNotIn("secret", public)

    def test_empty_success_becomes_failure(self):
        candidate = _candidates([rec(text="")], "fused")[1]
        self.assertIn("keinen Text", candidate["error"])

    def test_markup_escapes_model_and_text(self):
        markup = build_recognition_section(
            [rec(model='"><script>x</script>', text="<b>raw</b>")], "doc", "fused")
        self.assertNotIn("<script>x</script>", markup)
        self.assertIn("&lt;b&gt;raw&lt;/b&gt;", markup)

    def test_dom_ids_are_unique_and_panels_match_candidates(self):
        markup = build_recognition_section([rec(), rec(), rec("trocr", text="", error="timeout")], "doc", "fused")
        dom = DOM(); dom.feed(markup)
        self.assertEqual(len(dom.ids), len(set(dom.ids)))
        self.assertEqual(len(dom.panels), 4)  # selected + three attempts

    def test_single_and_multi_page_candidates_keep_page_provenance(self):
        single = build_recognition_section(
            [rec(page="folio-1")], "doc", "fused")
        multi = build_recognition_section(
            [rec(page="folio-1"), rec(model="model-2", page="folio-2")],
            "doc", "fused",
        )
        self.assertIn('data-page="folio-1"', single)
        self.assertIn('data-page="folio-1"', multi)
        self.assertIn('data-page="folio-2"', multi)

    def test_missing_page_is_explicit(self):
        markup = build_recognition_section([rec()], "doc", "fused")
        self.assertIn("Nicht zugeordnet", markup)

    def test_explanation_blocks_have_deterministic_order(self):
        first = build_recognition_section([rec()], "doc", "fused")
        second = build_recognition_section([rec()], "doc", "fused")
        labels = (
            "engine_confidence", "agreement", "degenerate", "failed",
            "reference_evaluation", "incomparable_confidence",
        )
        for markup in (first, second):
            positions = [markup.index(f'id="quality-explanation-{label}') for label in labels]
            self.assertEqual(positions, sorted(positions))

    def test_duplicate_models_remain_independently_reachable(self):
        markup = build_recognition_section(
            [rec(page="one"), rec(page="two")], "doc", "fused")
        dom = DOM(); dom.feed(markup)
        candidate_panels = [
            panel for panel in dom.panels
            if panel["data-recognition-panel"] != "selected"
        ]
        self.assertEqual(len(candidate_panels), 2)
        self.assertEqual(
            len({panel["data-recognition-panel"] for panel in candidate_panels}),
            2,
        )

    def test_no_js_panels_are_semantic_details(self):
        markup = build_recognition_section([rec(), rec("kraken")], "doc", "fused")
        self.assertEqual(markup.count('<details class="rec-panel"'), 3)
        self.assertIn("<summary>", markup)

    def test_failed_candidate_has_no_download(self):
        markup = build_recognition_section([rec("trocr", text="", error="timeout")], "doc", "fused")
        failed = markup.split('data-recognition-panel="trocr-model"', 1)[1]
        self.assertNotIn("rec-download\" href", failed)
        self.assertIn("Kein Textdownload verfügbar", failed)

    def test_comparison_shell_is_opt_in_and_accessibly_labelled(self):
        markup = build_recognition_section([rec(), rec("kraken")], "doc", "fused")
        self.assertIn("data-recognition-compare", markup)
        self.assertIn("data-rec-compare-panes hidden", markup)
        self.assertIn('for="rec-compare-select-left">Version links', markup)
        self.assertIn('for="rec-compare-select-right">Version rechts', markup)

    def test_comparison_options_are_page_scoped_and_failures_disabled(self):
        markup = build_recognition_section([
            rec(page="p1"),
            rec("kraken", page="p2"),
            rec("trocr", text="", error="timeout", page="p2"),
        ], "doc", "fused")
        self.assertIn('data-page="p1"', markup)
        self.assertIn('data-page="p2"', markup)
        failed_id = _candidates([
            rec(page="p1"), rec("kraken", page="p2"),
            rec("trocr", text="", error="timeout", page="p2"),
        ], "fused")[-1]["id"]
        self.assertIn(f'value="{failed_id}" data-page="p2" disabled', markup)

    def test_download_only_when_artifact_exists(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "recognitions").mkdir()
            (root / "recognitions" / "fused.txt").write_text("fused")
            markup = build_recognition_section([rec()], "doc", "fused", root)
        self.assertEqual(markup.count("Diese Transkription herunterladen"), 1)


if __name__ == "__main__":
    unittest.main()
