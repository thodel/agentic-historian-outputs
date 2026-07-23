"""Tests for quality tooltip reader-appropriateness (issue #123).

Visitor-facing tooltips (quality explanation texts) must not contain
imperative maintenance instructions directed at technical maintainers.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "scripts"))


# Imperative phrases that indicate maintainer instructions, not reader guidance
_MAINTAINER_PHRASES = [
    "Ersetzen Sie",
    "ersetzen Sie",
    "verwenden Sie stattdessen",
    "Bitte verwenden",
    "sollten Sie",
    "müssen Sie",
]


def test_no_maintainer_instructions_in_explanations():
    """EXPLANATIONS registry must not contain imperative maintainer instructions."""
    from quality import EXPLANATIONS
    violations = []
    for key, (short_label, body) in EXPLANATIONS.items():
        for phrase in _MAINTAINER_PHRASES:
            if phrase in body:
                violations.append(f"EXPLANATIONS['{key}'] contains '{phrase}': ...{body[max(0,body.index(phrase)-20):body.index(phrase)+60]}...")
    assert not violations, "Visitor-facing tooltips must not contain maintainer instructions:\n" + "\n".join(violations)


def test_legacy_qa_tooltip_explains_for_readers():
    """The legacy_qa tooltip must explain what the value is and what to rely on instead."""
    from quality import EXPLANATIONS
    _, body = EXPLANATIONS["legacy_qa"]
    assert "keine" in body.lower() or "kein" in body.lower(), \
        "legacy_qa tooltip must state what the value cannot tell (negative framing for reader)"
    assert "konfidenz" in body.lower() or "cer" in body.lower() or "erkennungsfehler" in body.lower(), \
        "legacy_qa tooltip must point readers to a reliable alternative"


def test_no_maintainer_phrases_in_generated_catalogue():
    """The generated catalogue index must not contain maintainer instruction phrases."""
    index = (ROOT / "docs/index.md").read_text(encoding="utf-8")
    violations = []
    for phrase in _MAINTAINER_PHRASES:
        if phrase in index:
            violations.append(phrase)
    assert not violations, f"Catalogue index contains maintainer phrases: {violations}"


def test_methodology_has_legacy_qa_maintainer_guidance():
    """Maintainer guidance for legacy_qa must live in methodology.md."""
    methodology = (ROOT / "docs/methodology.md").read_text(encoding="utf-8")
    assert "legacy-qa" in methodology.lower() or "legacy_qa" in methodology.lower() or "qa_score" in methodology, \
        "methodology.md must document the legacy QA field for maintainers"
    # Check it uses the anchor for stable linking
    assert "quality-metrics-legacy" in methodology, \
        "methodology.md must have a stable anchor for the legacy-QA section"


if __name__ == "__main__":
    test_no_maintainer_instructions_in_explanations()
    test_legacy_qa_tooltip_explains_for_readers()
    test_no_maintainer_phrases_in_generated_catalogue()
    test_methodology_has_legacy_qa_maintainer_guidance()
    print("All tests passed!")
