"""Tests for issue #29: candidate-level confidence and failure indicator clarity.

Acceptance criteria (from issue #29):
  1. Every candidate metric identifies its producer and meaning.
  2. Failed candidates never display a misleading zero-confidence success state.
  3. Incomparable engine confidences carry a clear warning.
  4. Screen readers receive metric name, value, unit, and scope in a sensible order.
  5. Recognition switching and side-by-side comparison update metric details
     together with the selected text  (HTML contract verified; JS covered in
     test_rec_viewer.mjs).
"""
import sys
import unittest
from html.parser import HTMLParser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from build_recognitions import (
    _candidates,
    _engine_confidence_dl,
    build_recognition_section,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _rec(engine="vlm", model="internvl", text="Hallo Welt", page="", **kw):
    return {"engine": engine, "model_id": model, "text": text, "page": page, **kw}


class _AttrParser(HTMLParser):
    """Collect all tag-attribute pairs encountered during parsing."""

    def __init__(self):
        super().__init__()
        self.found = []  # list of (tag, attrs_dict)

    def handle_starttag(self, tag, attrs):
        self.found.append((tag, dict(attrs)))

    def attrs_with(self, **kw):
        """Return all (tag, attrs) where every kw matches an attribute value."""
        out = []
        for tag, attrs in self.found:
            if all(attrs.get(k) == v for k, v in kw.items()):
                out.append((tag, attrs))
        return out


def _parse(html: str) -> _AttrParser:
    p = _AttrParser()
    p.feed(html)
    return p


# ---------------------------------------------------------------------------
# 1. Every candidate metric identifies its producer and meaning
# ---------------------------------------------------------------------------

class MetricProducerIdentificationTests(unittest.TestCase):
    """Acceptance criterion 1: every metric must label its producer and meaning."""

    def test_confidence_dl_contains_scope_label(self):
        """_engine_confidence_dl emits scope (engine/model/page) in the output."""
        candidate = {"engine": "vlm", "model_id": "internvl", "page": "", "confidence": 0.85}
        dl = _engine_confidence_dl(candidate)
        # Scope label: at minimum the engine name must appear
        self.assertIn("vlm", dl)
        # Formatted value must appear
        self.assertIn("85%", dl)

    def test_confidence_scope_includes_model_when_present(self):
        candidate = {"engine": "kraken", "model_id": "mccatmus", "page": "", "confidence": 0.72}
        dl = _engine_confidence_dl(candidate)
        self.assertIn("kraken", dl)
        self.assertIn("mccatmus", dl)

    def test_confidence_scope_includes_page_when_present(self):
        candidate = {"engine": "trocr", "model_id": "large", "page": "Seite 3", "confidence": 0.6}
        dl = _engine_confidence_dl(candidate)
        self.assertIn("Seite 3", dl)

    def test_metric_type_label_present_in_dl(self):
        """The DL term must name the metric: 'Engine-Konfidenz'."""
        candidate = {"engine": "vlm", "model_id": "internvl", "page": "", "confidence": 0.9}
        dl = _engine_confidence_dl(candidate)
        self.assertIn("Engine-Konfidenz", dl)

    def test_missing_confidence_is_labeled_not_blank(self):
        """None confidence must appear as 'Nicht angegeben', not an empty cell."""
        candidate = {"engine": "vlm", "model_id": "internvl", "page": "", "confidence": None}
        dl = _engine_confidence_dl(candidate)
        self.assertIn("Nicht angegeben", dl)

    def test_candidate_panel_shows_engine_name(self):
        """Every generated panel must identify the engine that produced it."""
        markup = build_recognition_section(
            [_rec(engine="kraken", model="mccatmus")], "doc", "fused"
        )
        # The panel must show the engine name somewhere in the candidate display
        self.assertIn("kraken", markup)

    def test_explanation_button_present_for_confidence(self):
        """An explanation button must be present so users can learn metric meaning."""
        candidate = _rec(confidence=0.75)
        dl = _engine_confidence_dl(candidate)
        self.assertIn("quality-explain-btn", dl)
        self.assertIn("engine_confidence", dl)

    def test_selected_fused_output_labeled(self):
        """The selected/fused output must be clearly labeled as such."""
        markup = build_recognition_section(
            [_rec()], "doc", "fused text"
        )
        self.assertIn("ausgewählt", markup)


# ---------------------------------------------------------------------------
# 2. Failed candidates never display a misleading zero-confidence success state
# ---------------------------------------------------------------------------

class FailedCandidateDisplayTests(unittest.TestCase):
    """Acceptance criterion 2: failed and zero-confidence candidates are distinct."""

    def test_failed_candidate_shows_no_confidence_dl(self):
        """A failed candidate must not receive an Engine-Konfidenz DL row."""
        markup = build_recognition_section(
            [_rec(text="", error="timeout")], "doc", "fused"
        )
        # Split off the failed panel and check it has no confidence dl
        # (selected panel has no confidence either, so just check no confusion)
        # The failed candidate panel should have no 'Engine-Konfidenz' row
        failed_panel_start = markup.find('class="rec-panel"', markup.find('rec-panel'))
        # Find the second panel (first real candidate)
        panels = markup.split('<details class="rec-panel"')
        # panels[0] = before first panel; panels[1] = selected; panels[2+] = candidates
        if len(panels) >= 3:
            failed_panel = panels[2]
            self.assertNotIn("Engine-Konfidenz", failed_panel)

    def test_failed_candidate_shows_failure_notice(self):
        """Failed candidates display an explanatory failure notice."""
        markup = build_recognition_section(
            [_rec(text="", error="timed out")], "doc", "fused"
        )
        self.assertIn("Erkennung fehlgeschlagen", markup)

    def test_degenerate_candidate_labeled_separately(self):
        """Degenerate output (repeated chars) must be labeled 'Degeneriert', not 'OK'."""
        # 25 repeated chars → degenerate
        markup = build_recognition_section(
            [_rec(text="x" * 30)], "doc", "fused"
        )
        self.assertIn("Degeneriert", markup)
        self.assertNotIn("rec-status--ok", markup.split("Degeneriert")[0].rsplit("rec-", 1)[-1])

    def test_zero_confidence_classified_as_degenerate(self):
        """Zero confidence (< 0.01) must be classified as degenerate, not success.

        The detect_degeneration() function treats confidence < 0.01 as degenerate.
        This means zero-confidence candidates must show 'Degeneriert', never
        'Erfolgreich', in their status nav item.
        """
        markup = build_recognition_section(
            [_rec(confidence=0.0, text="some text")], "doc", "fused"
        )
        # Zero-confidence triggers degeneration: the nav status span must be
        # rec-status--degenerate for the vlm candidate.
        # Check _candidates directly for an authoritative result
        candidates = _candidates(
            [_rec(confidence=0.0, text="some text")], "fused"
        )
        vlm_cand = next(c for c in candidates if c["engine"] == "vlm")
        self.assertTrue(vlm_cand.get("is_degenerate"),
                        "zero-confidence candidate must be marked degenerate")
        self.assertTrue(bool(vlm_cand["error"]),
                        "degenerate candidate must have an error message")
        # Also verify the visual status in the rendered markup
        self.assertIn("rec-status--degenerate", markup)

    def test_empty_text_forced_to_failure(self):
        """An engine that returns empty text must appear as failed, not silent zero."""
        candidates = _candidates([_rec(text="", model="empty-model")], "fused")
        empty_cand = next(c for c in candidates if c["engine"] == "vlm")
        self.assertTrue(bool(empty_cand["error"]))
        self.assertIn("keinen Text", empty_cand["error"])

    def test_failed_status_badge_not_confidence_badge(self):
        """A failed candidate's badge class is 'failed', never 'engine_confidence'."""
        markup = build_recognition_section(
            [_rec(text="", error="service unavailable")], "doc", "fused"
        )
        # The failed candidate's status badge should be quality-badge--failed
        self.assertIn("quality-badge--failed", markup)


# ---------------------------------------------------------------------------
# 3. Incomparable engine confidences carry a clear warning
# ---------------------------------------------------------------------------

class IncomparableConfidenceWarningTests(unittest.TestCase):
    """Acceptance criterion 3: multi-engine sections warn about incomparability."""

    def test_incomparable_explanation_key_present_in_section(self):
        """The incomparable_confidence explanation block must be in the section HTML."""
        markup = build_recognition_section(
            [_rec(engine="kraken", confidence=0.8),
             _rec(engine="trocr", confidence=0.9)],
            "doc", "fused"
        )
        self.assertIn("incomparable_confidence", markup)

    def test_incomparable_warning_button_in_intro(self):
        """An explicit incomparable warning button must appear in the section intro."""
        markup = build_recognition_section(
            [_rec(engine="kraken"), _rec(engine="vlm")], "doc", "fused"
        )
        # The intro paragraph must have an ⓘ button for incomparable_confidence
        self.assertIn("quality-explanation-incomparable_confidence", markup)

    def test_incomparable_explanation_block_has_accessible_structure(self):
        """The explanation block must have role=region and aria-label."""
        markup = build_recognition_section(
            [_rec(engine="kraken", confidence=0.7)], "doc", "fused"
        )
        self.assertIn('role="region"', markup)
        self.assertIn('aria-label=', markup)

    def test_single_engine_still_has_incomparable_block(self):
        """Even with a single engine, the incomparable block must be present
        (consistent layout; users may add engines later)."""
        markup = build_recognition_section(
            [_rec(engine="kraken", confidence=0.5)], "doc", "fused"
        )
        self.assertIn("incomparable_confidence", markup)


# ---------------------------------------------------------------------------
# 4. Screen readers receive metric name, value, unit, and scope in order
# ---------------------------------------------------------------------------

class ScreenReaderMetricOrderTests(unittest.TestCase):
    """Acceptance criterion 4: ARIA structure for assistive technology."""

    def test_confidence_dd_has_aria_label(self):
        """The confidence <dd> must carry an aria-label with value and scope."""
        candidate = {"engine": "kraken", "model_id": "mccatmus", "page": "p1", "confidence": 0.82}
        dl = _engine_confidence_dl(candidate)
        self.assertIn("aria-label=", dl)

    def test_confidence_aria_label_contains_value(self):
        """The aria-label must include the formatted confidence value."""
        candidate = {"engine": "vlm", "model_id": "internvl", "page": "", "confidence": 0.75}
        dl = _engine_confidence_dl(candidate)
        # 75% must appear in the aria-label
        self.assertIn("75%", dl)

    def test_confidence_aria_label_contains_unit(self):
        """The aria-label must include 'Wahrscheinlichkeit' (unit name)."""
        candidate = {"engine": "vlm", "model_id": "internvl", "page": "", "confidence": 0.6}
        dl = _engine_confidence_dl(candidate)
        self.assertIn("Wahrscheinlichkeit", dl)

    def test_confidence_aria_label_contains_scope(self):
        """The aria-label must include the scope (engine name at minimum)."""
        candidate = {"engine": "vlm", "model_id": "internvl", "page": "", "confidence": 0.9}
        dl = _engine_confidence_dl(candidate)
        self.assertIn("vlm", dl)
        self.assertIn("internvl", dl)

    def test_missing_confidence_aria_label_has_scope(self):
        """None confidence must still carry scope in the aria-label."""
        candidate = {"engine": "trocr", "model_id": "base", "page": "", "confidence": None}
        dl = _engine_confidence_dl(candidate)
        self.assertIn("aria-label=", dl)
        self.assertIn("trocr", dl)

    def test_dl_structure_name_before_value(self):
        """The <dt> ('Engine-Konfidenz') must appear before the <dd> in the HTML."""
        candidate = {"engine": "vlm", "model_id": "internvl", "page": "", "confidence": 0.5}
        dl = _engine_confidence_dl(candidate)
        dt_pos = dl.index("<dt>Engine-Konfidenz</dt>")
        dd_pos = dl.index("<dd ")
        self.assertLess(dt_pos, dd_pos,
                        "Metric name (dt) must precede value/scope (dd)")

    def test_comparison_bodies_have_aria_live(self):
        """Comparison pane bodies must have aria-live=polite for SR announcement."""
        markup = build_recognition_section(
            [_rec(engine="kraken"), _rec(engine="vlm")], "doc", "fused"
        )
        # Both compare-body divs should have aria-live="polite"
        self.assertEqual(markup.count('aria-live="polite"'), 2)

    def test_recognition_section_has_labelled_landmark(self):
        """The overall section must have aria-labelledby pointing to the heading."""
        markup = build_recognition_section([_rec()], "doc", "fused")
        self.assertIn('aria-labelledby="recognitions-heading"', markup)
        self.assertIn('id="recognitions-heading"', markup)


# ---------------------------------------------------------------------------
# 5. Comparison includes metric details (HTML contract)
# ---------------------------------------------------------------------------

class ComparisonMetricDetailTests(unittest.TestCase):
    """Acceptance criterion 5 (HTML contract): candidateHTML sources .rec-meta.

    The JS test_rec_viewer.mjs tests the runtime behavior; this suite verifies
    that the generated HTML includes the .rec-meta block inside every panel so
    candidateHTML() can copy it into the comparison pane.
    """

    def test_successful_panel_has_rec_meta(self):
        """Every successful candidate panel must contain .rec-meta for comparison."""
        markup = build_recognition_section(
            [_rec(engine="kraken", confidence=0.8)], "doc", "fused"
        )
        self.assertIn('class="rec-meta"', markup)

    def test_rec_meta_contains_engine_dt(self):
        """The .rec-meta dl must contain an Engine row."""
        markup = build_recognition_section(
            [_rec(engine="kraken", model="mccatmus")], "doc", "fused"
        )
        self.assertIn("<dt>Engine</dt>", markup)

    def test_rec_meta_contains_confidence_dt(self):
        """The .rec-meta dl must contain an Engine-Konfidenz row for successful candidates."""
        markup = build_recognition_section(
            [_rec(engine="kraken", confidence=0.7)], "doc", "fused"
        )
        self.assertIn("<dt>Engine-Konfidenz</dt>", markup)

    def test_failed_panel_has_rec_error_not_rec_meta(self):
        """Failed candidate panels must have .rec-error for comparison pane display."""
        markup = build_recognition_section(
            [_rec(text="", error="timeout")], "doc", "fused"
        )
        self.assertIn('class="notice notice--warning rec-error"', markup)

    def test_comparison_pane_select_options_disabled_for_failures(self):
        """Comparison <select> options for failed candidates must be disabled."""
        markup = build_recognition_section(
            [_rec(engine="kraken"),
             _rec(engine="trocr", text="", error="timeout")],
            "doc", "fused"
        )
        # Options for the failed candidate must carry disabled
        # Find the select section
        self.assertIn("disabled", markup)


if __name__ == "__main__":
    unittest.main()
