"""Tests for accessible explanations for quality metrics (issue #30).

Covers:
- METHODOLOGY_ANCHORS completeness and format
- explanation_block() includes methodology links resolving to stable anchors
- selection_score explanation key exists with required content
- explanation_block() keyboard/screen-reader attributes
- quality_badge() uses short label in title (no hover-only critical text)
- Same explanation keys reused across catalogue, document, and comparison views
- build_recognition_section() includes all required explanation keys
- Catalogue card HTML includes reference_evaluation explanation
- Document header HTML includes explanation blocks for used keys
- No unique critical meaning is conveyed only via title attribute
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from quality import (
    EXPLANATIONS,
    METHODOLOGY_ANCHORS,
    explanation_block,
    explanation_button,
    quality_badge,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _rec(engine="kraken", model="catmus", page="p001", confidence=0.8, error=None, text="hello"):
    """Minimal recognition candidate dict."""
    return {
        "engine": engine,
        "model_id": model,
        "page": page,
        "text": text,
        "confidence": confidence,
        "error": error or "",
    }


# ---------------------------------------------------------------------------
# Suite 1: METHODOLOGY_ANCHORS completeness
# ---------------------------------------------------------------------------

class MethodologyAnchorTests(unittest.TestCase):
    """METHODOLOGY_ANCHORS must cover all explanation keys and resolve correctly."""

    # All keys that must have a methodology anchor
    REQUIRED_KEYS = {
        "engine_confidence",
        "agreement",
        "reference_evaluation",
        "degenerate",
        "failed",
        "missing",
        "legacy_qa",
        "incomparable_confidence",
        "verification_needed",
        "selection_score",
    }

    def test_all_required_keys_have_anchors(self):
        """Every required explanation key must have a METHODOLOGY_ANCHORS entry."""
        for key in self.REQUIRED_KEYS:
            self.assertIn(key, METHODOLOGY_ANCHORS,
                          f"{key!r} missing from METHODOLOGY_ANCHORS")

    def test_anchors_are_absolute_paths(self):
        """Anchor URLs must be absolute paths starting with /methodology/#."""
        for key, url in METHODOLOGY_ANCHORS.items():
            self.assertTrue(
                url.startswith("/methodology/#"),
                f"METHODOLOGY_ANCHORS[{key!r}] = {url!r} does not start with "
                f"'/methodology/#'; must be an absolute path for cross-depth resolution",
            )

    def test_anchor_ids_valid_css_identifiers(self):
        """Fragment IDs must be valid HTML anchor ids (ASCII alphanumeric + hyphens)."""
        for key, url in METHODOLOGY_ANCHORS.items():
            fragment = url.split("#", 1)[1] if "#" in url else ""
            self.assertTrue(
                re.match(r"^[a-z][a-z0-9-]*$", fragment),
                f"METHODOLOGY_ANCHORS[{key!r}] fragment {fragment!r} is not a "
                f"valid lowercase hyphen-separated anchor id",
            )

    def test_selection_score_anchor_distinct_section(self):
        """selection_score must have its own dedicated section anchor."""
        anchor = METHODOLOGY_ANCHORS.get("selection_score", "")
        self.assertIn("selection-score", anchor,
                      "selection_score anchor must point to a selection-score section")

    def test_all_methodology_anchors_present_in_methodology_md(self):
        """Every anchor used in METHODOLOGY_ANCHORS must exist in docs/methodology.md."""
        md_path = Path(__file__).parent.parent / "docs" / "methodology.md"
        self.assertTrue(md_path.exists(), "docs/methodology.md must exist")
        content = md_path.read_text(encoding="utf-8")
        unique_fragments = {url.split("#", 1)[1] for url in METHODOLOGY_ANCHORS.values() if "#" in url}
        for fragment in unique_fragments:
            self.assertIn(
                f'id="{fragment}"',
                content,
                f"Anchor id=\"{fragment}\" not found in docs/methodology.md; "
                f"add <a id=\"{fragment}\"></a> to the methodology section",
            )


# ---------------------------------------------------------------------------
# Suite 2: explanation_block() accessibility
# ---------------------------------------------------------------------------

class ExplanationBlockAccessibilityTests(unittest.TestCase):
    """explanation_block() output must meet keyboard/screen-reader criteria."""

    def test_block_has_role_region(self):
        """Explanation block must have role=region for landmark navigation."""
        html = explanation_block("engine_confidence", "t1")
        self.assertIn('role="region"', html,
                      "explanation_block must carry role=region for landmark navigation")

    def test_block_has_aria_label(self):
        """Explanation block must have aria-label matching the short explanation label."""
        short_label = EXPLANATIONS["engine_confidence"][0]
        html = explanation_block("engine_confidence", "t2")
        self.assertIn(f'aria-label="{short_label}"', html,
                      "explanation_block aria-label must match the explanation short label")

    def test_block_is_hidden_by_default(self):
        """Explanation block must start hidden (toggled by button)."""
        html = explanation_block("agreement", "t3")
        self.assertIn(" hidden", html,
                      "explanation_block must carry the hidden attribute by default")

    def test_block_has_unique_id(self):
        """explanation_block must have a unique id for aria-controls linkage."""
        html = explanation_block("reference_evaluation", "mySuffix")
        self.assertIn('id="quality-explanation-reference_evaluation-mySuffix"', html)

    def test_block_contains_body_text(self):
        """Explanation block must contain the registered body text."""
        _, body = EXPLANATIONS["agreement"]
        html = explanation_block("agreement", "t4")
        # Body text may be split across elements; check for a substring
        self.assertIn(body[:40], html,
                      "explanation_block must include the registered explanation body")

    def test_block_contains_methodology_link(self):
        """explanation_block must include a methodology link for keys with anchors."""
        html = explanation_block("engine_confidence", "t5")
        self.assertIn('quality-explanation-link', html,
                      "explanation_block must include a methodology link element")
        self.assertIn('/methodology/#', html,
                      "explanation_block methodology link must point to /methodology/#...")

    def test_block_methodology_link_matches_anchor(self):
        """The methodology link href in explanation_block must match METHODOLOGY_ANCHORS."""
        key = "reference_evaluation"
        expected_href = METHODOLOGY_ANCHORS[key]
        html = explanation_block(key, "t6")
        self.assertIn(f'href="{expected_href}"', html,
                      f"explanation_block href must be {expected_href!r}")

    def test_block_missing_key_returns_empty(self):
        """Unknown key must return an empty string."""
        self.assertEqual("", explanation_block("nonexistent_key_xyz"))

    def test_methodology_link_has_visible_text(self):
        """The methodology link must have visible text (not just hidden/icon text)."""
        html = explanation_block("degenerate", "t7")
        # The link should contain at least the text "Methodik"
        self.assertIn("Methodik", html,
                      "Methodology link must contain visible link text 'Methodik'")

    def test_methodology_link_arrow_is_aria_hidden(self):
        """The decorative arrow in the methodology link must be aria-hidden."""
        html = explanation_block("failed", "t8")
        self.assertIn('aria-hidden="true"', html,
                      "Decorative arrow in methodology link must be aria-hidden")


# ---------------------------------------------------------------------------
# Suite 3: explanation_button() accessibility
# ---------------------------------------------------------------------------

class ExplanationButtonAccessibilityTests(unittest.TestCase):
    """explanation_button() output must be keyboard/touch/screen-reader accessible."""

    def test_button_is_native_button_element(self):
        """Must use <button> element for native keyboard/focus semantics."""
        html = explanation_button("engine_confidence", "b1")
        self.assertTrue(
            html.strip().startswith("<button"),
            "explanation_button must produce a <button> element",
        )

    def test_button_has_type_button(self):
        """Button must have type=button to prevent accidental form submission."""
        html = explanation_button("engine_confidence", "b2")
        self.assertIn('type="button"', html)

    def test_button_has_aria_expanded(self):
        """Button must have aria-expanded for toggle state announcement."""
        html = explanation_button("agreement", "b3")
        self.assertIn("aria-expanded=", html)

    def test_button_has_aria_controls(self):
        """Button must have aria-controls pointing to the explanation block id."""
        html = explanation_button("reference_evaluation", "ctrl1")
        self.assertIn('aria-controls="quality-explanation-reference_evaluation-ctrl1"', html)

    def test_button_icon_is_aria_hidden(self):
        """The ⓘ icon in the button must be aria-hidden to avoid duplicate announcements."""
        html = explanation_button("degenerate", "b5")
        self.assertIn('aria-hidden="true"', html)

    def test_button_has_visible_text(self):
        """Button must have visible text (short explanation label) for sighted users."""
        short_label = EXPLANATIONS["failed"][0]
        html = explanation_button("failed", "b6")
        self.assertIn(short_label, html)


# ---------------------------------------------------------------------------
# Suite 4: quality_badge() hover-only safety
# ---------------------------------------------------------------------------

class QualityBadgeHoverSafetyTests(unittest.TestCase):
    """quality_badge() must not convey critical meaning only via hover (title attr)."""

    def test_badge_title_uses_short_label_not_body(self):
        """title= attribute must use short label, not the full explanation body."""
        short_label, body = EXPLANATIONS["engine_confidence"]
        html = quality_badge("engine_confidence", 0.75, "probability", "kraken/catmus/p001")
        # short label should be in title
        self.assertIn(f'title="{short_label}"', html,
                      "quality_badge title= must use the short label")
        # full body must NOT be in title (hover-only critical text forbidden)
        self.assertNotIn(body[:60], html,
                         "quality_badge must not put full explanation body in title= attribute")

    def test_badge_title_does_not_contain_full_body_for_agreement(self):
        short_label, body = EXPLANATIONS["agreement"]
        html = quality_badge("agreement", 0.75, "ratio", "candidate")
        self.assertNotIn(body[:60], html)

    def test_failed_badge_title_is_short_label(self):
        short_label, _ = EXPLANATIONS["failed"]
        html = quality_badge("failed", None, "n/a", "n/a")
        self.assertIn(f'title="{short_label}"', html)

    def test_degenerate_badge_title_is_short_label(self):
        short_label, _ = EXPLANATIONS["degenerate"]
        html = quality_badge("degenerate", None, "n/a", "n/a")
        self.assertIn(f'title="{short_label}"', html)


# ---------------------------------------------------------------------------
# Suite 5: selection_score explanation key
# ---------------------------------------------------------------------------

class SelectionScoreExplanationTests(unittest.TestCase):
    """selection_score explanation must exist and meet content requirements."""

    def test_selection_score_in_explanations(self):
        """selection_score must be registered in EXPLANATIONS."""
        self.assertIn("selection_score", EXPLANATIONS,
                      "selection_score explanation key missing from EXPLANATIONS registry")

    def test_selection_score_has_short_label(self):
        """selection_score short label must be non-empty and ≤80 chars."""
        short, _ = EXPLANATIONS["selection_score"]
        self.assertTrue(short, "selection_score short label must be non-empty")
        self.assertLessEqual(len(short), 80, "selection_score short label must be ≤80 chars")

    def test_selection_score_body_explains_fusion(self):
        """Body text must explain that selected result is a pipeline choice."""
        _, body = EXPLANATIONS["selection_score"]
        lowered = body.lower()
        self.assertTrue(
            "ausgew" in lowered or "fusion" in lowered or "pipeline" in lowered,
            "selection_score body must explain the selection/fusion concept",
        )

    def test_selection_score_body_mentions_verification(self):
        """Body must warn that selected result still needs verification."""
        _, body = EXPLANATIONS["selection_score"]
        lowered = body.lower()
        self.assertTrue(
            "überprüf" in lowered or "original" in lowered,
            "selection_score body must mention the need to verify against original",
        )

    def test_selection_score_body_mentions_incomparability(self):
        """Body must note that engine confidences are not summed/averaged across engines."""
        _, body = EXPLANATIONS["selection_score"]
        self.assertTrue(
            "konfidenz" in body.lower() or "engines" in body.lower(),
            "selection_score body must mention engine confidence incomparability",
        )

    def test_selection_score_has_methodology_anchor(self):
        """selection_score must have an entry in METHODOLOGY_ANCHORS."""
        self.assertIn("selection_score", METHODOLOGY_ANCHORS,
                      "selection_score must have a METHODOLOGY_ANCHORS entry")


# ---------------------------------------------------------------------------
# Suite 6: explanation keys reused across views
# ---------------------------------------------------------------------------

class ExplanationKeyReuseTests(unittest.TestCase):
    """The same EXPLANATIONS keys must be used in build_recognitions, build_outputs,
    and build_index (catalogue, document, and comparison views)."""

    def _load_source(self, filename: str) -> str:
        path = Path(__file__).parent.parent / "scripts" / filename
        return path.read_text(encoding="utf-8")

    def test_recognition_viewer_uses_engine_confidence_key(self):
        src = self._load_source("build_recognitions.py")
        self.assertIn('"engine_confidence"', src,
                      "build_recognitions.py must use engine_confidence explanation key")

    def test_recognition_viewer_uses_agreement_key(self):
        src = self._load_source("build_recognitions.py")
        self.assertIn('"agreement"', src,
                      "build_recognitions.py must use agreement explanation key")

    def test_recognition_viewer_uses_selection_score_key(self):
        src = self._load_source("build_recognitions.py")
        self.assertIn('"selection_score"', src,
                      "build_recognitions.py must include selection_score explanation key")

    def test_recognition_viewer_uses_reference_evaluation_key(self):
        src = self._load_source("build_recognitions.py")
        self.assertIn('"reference_evaluation"', src,
                      "build_recognitions.py must use reference_evaluation explanation key")

    def test_recognition_viewer_uses_incomparable_confidence_key(self):
        src = self._load_source("build_recognitions.py")
        self.assertIn('"incomparable_confidence"', src,
                      "build_recognitions.py must use incomparable_confidence explanation key")

    def test_document_page_uses_verification_needed_key(self):
        src = self._load_source("build_outputs.py")
        self.assertIn('"verification_needed"', src,
                      "build_outputs.py must use verification_needed explanation key")

    def test_document_page_uses_legacy_qa_key(self):
        src = self._load_source("build_outputs.py")
        self.assertIn('"legacy_qa"', src,
                      "build_outputs.py must use legacy_qa explanation key")

    def test_catalogue_uses_reference_evaluation_key(self):
        src = self._load_source("build_index.py")
        self.assertIn('"reference_evaluation"', src,
                      "build_index.py (catalogue) must use reference_evaluation explanation key")

    def test_all_views_import_explanation_helpers(self):
        """All three builder modules must import explanation_button and explanation_block."""
        for filename in ("build_recognitions.py", "build_outputs.py", "build_index.py"):
            src = self._load_source(filename)
            self.assertIn("explanation_button", src,
                          f"{filename} must import/use explanation_button")
            self.assertIn("explanation_block", src,
                          f"{filename} must import/use explanation_block")


# ---------------------------------------------------------------------------
# Suite 7: build_recognition_section() integration
# ---------------------------------------------------------------------------

class RecognitionSectionExplanationTests(unittest.TestCase):
    """build_recognition_section() must include all required explanation blocks."""

    def _section(self, candidates=None, transcript="fused"):
        from build_recognitions import build_recognition_section
        cands = candidates or [_rec()]
        return build_recognition_section(cands, "test-doc", transcript)

    def test_section_includes_engine_confidence_explanation(self):
        html = self._section()
        self.assertIn("engine_confidence", html,
                      "Recognition section must include engine_confidence explanation")

    def test_section_includes_incomparable_confidence_explanation(self):
        html = self._section()
        self.assertIn("incomparable_confidence", html,
                      "Recognition section must include incomparable_confidence explanation")

    def test_section_includes_reference_evaluation_explanation(self):
        html = self._section()
        self.assertIn("reference_evaluation", html,
                      "Recognition section must include reference_evaluation explanation")

    def test_section_includes_degenerate_explanation(self):
        html = self._section()
        self.assertIn("degenerate", html,
                      "Recognition section must include degenerate explanation")

    def test_section_includes_failed_explanation(self):
        html = self._section()
        self.assertIn("failed", html,
                      "Recognition section must include failed explanation")

    def test_section_includes_selection_score_explanation(self):
        html = self._section()
        self.assertIn("selection_score", html,
                      "Recognition section must include selection_score explanation for the fused candidate")

    def test_selected_candidate_has_selection_score_button(self):
        """The selected/fused candidate summary must contain the selection_score button."""
        html = self._section()
        # The button class and key must be present in the section
        self.assertIn("quality-explain-btn", html)
        self.assertIn("selection_score", html)

    def test_all_explanation_blocks_have_methodology_links(self):
        """Every explanation block in the section must contain a methodology link."""
        html = self._section()
        # Find all quality-explanation divs
        blocks = re.findall(
            r'<div class="quality-explanation"[^>]*hidden>(.*?)</div>',
            html, re.DOTALL,
        )
        self.assertTrue(blocks, "Must find at least one explanation block in section")
        for i, block in enumerate(blocks):
            self.assertIn(
                "/methodology/",
                block,
                f"Explanation block #{i} in recognition section missing methodology link",
            )


# ---------------------------------------------------------------------------
# Suite 8: methodology.md stable anchors
# ---------------------------------------------------------------------------

class MethodologyDocumentTests(unittest.TestCase):
    """docs/methodology.md must have stable anchors for all required sections."""

    REQUIRED_ANCHORS = [
        "quality-metrics",
        "quality-metrics-engine-confidence",
        "quality-metrics-agreement",
        "quality-metrics-reference-evaluation",
        "quality-metrics-degeneration",
        "quality-metrics-failure",
        "quality-metrics-selection-score",
        "quality-metrics-verification",
    ]

    @classmethod
    def setUpClass(cls):
        md_path = Path(__file__).parent.parent / "docs" / "methodology.md"
        cls.content = md_path.read_text(encoding="utf-8")

    def test_required_anchors_present(self):
        for anchor in self.REQUIRED_ANCHORS:
            with self.subTest(anchor=anchor):
                self.assertIn(
                    f'id="{anchor}"',
                    self.content,
                    f'Anchor id="{anchor}" missing from docs/methodology.md',
                )

    def test_quality_metrics_section_is_comprehensible(self):
        """Quality metrics section must mention key terms researchers need."""
        lowered = self.content.lower()
        for term in ("konfidenz", "übereinstimmung", "cer", "degeneri", "verifikation", "fusion"):
            self.assertIn(term, lowered,
                          f"methodology.md quality metrics section must mention '{term}'")

    def test_agreement_section_states_not_correctness(self):
        """Agreement section must explicitly say agreement ≠ correctness."""
        lowered = self.content.lower()
        self.assertTrue(
            "übereinstimmung" in lowered and "korrekt" in lowered,
            "methodology.md must state that agreement does not establish correctness",
        )

    def test_engine_confidence_section_mentions_incomparability(self):
        """Confidence section must say values from different engines are not comparable."""
        lowered = self.content.lower()
        self.assertTrue(
            "nicht" in lowered and "vergleich" in lowered,
            "methodology.md must mention that engine confidence values are not comparable",
        )

    def test_reference_evaluation_mentions_reference_requirement(self):
        """CER/WER section must state a reference is required."""
        self.assertIn("Referenz", self.content,
                      "methodology.md must mention 'Referenz' in the CER/WER section")

    def test_verification_section_is_categorical(self):
        """Verification section must list the status values."""
        self.assertIn("machine-generated", self.content,
                      "methodology.md must list machine-generated as a verification status")
        self.assertIn("human-verified", self.content,
                      "methodology.md must list human-verified as a verification status")


if __name__ == "__main__":
    unittest.main()
