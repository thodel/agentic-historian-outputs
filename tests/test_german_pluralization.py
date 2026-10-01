"""Tests for German pluralization helper and typo fixes (issue #121)."""

from __future__ import annotations

import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "scripts"))


# ---------------------------------------------------------------------------
# de_plural helper: n=0, 1, 2 for every count string
# ---------------------------------------------------------------------------

class GermanPluralizationTests(unittest.TestCase):
    def test_de_plural_failed_attempts(self):
        from quality import de_plural
        assert de_plural(0, "fehlgeschlagener Erkennungsversuch", "fehlgeschlagene Erkennungsversuche") == "0 fehlgeschlagene Erkennungsversuche"
        assert de_plural(1, "fehlgeschlagener Erkennungsversuch", "fehlgeschlagene Erkennungsversuche") == "1 fehlgeschlagener Erkennungsversuch"
        assert de_plural(2, "fehlgeschlagener Erkennungsversuch", "fehlgeschlagene Erkennungsversuche") == "2 fehlgeschlagene Erkennungsversuche"


    def test_de_plural_degenerate_results(self):
        from quality import de_plural
        assert de_plural(0, "degeneriertes Ergebnis", "degenerierte Ergebnisse") == "0 degenerierte Ergebnisse"
        assert de_plural(1, "degeneriertes Ergebnis", "degenerierte Ergebnisse") == "1 degeneriertes Ergebnis"
        assert de_plural(2, "degeneriertes Ergebnis", "degenerierte Ergebnisse") == "2 degenerierte Ergebnisse"


    def test_de_plural_pages(self):
        from quality import de_plural
        assert de_plural(0, "Seite", "Seiten") == "0 Seiten"
        assert de_plural(1, "Seite", "Seiten") == "1 Seite"
        assert de_plural(2, "Seite", "Seiten") == "2 Seiten"


    def test_de_plural_recognition_problems(self):
        from quality import de_plural
        assert de_plural(0, "Erkennungsproblem", "Erkennungsprobleme") == "0 Erkennungsprobleme"
        assert de_plural(1, "Erkennungsproblem", "Erkennungsprobleme") == "1 Erkennungsproblem"
        assert de_plural(2, "Erkennungsproblem", "Erkennungsprobleme") == "2 Erkennungsprobleme"


    # ---------------------------------------------------------------------------
    # Generated pages must not contain stale text
    # ---------------------------------------------------------------------------

    def test_no_antwortierte_in_generated_pages(self):
        """No generated page must contain the typo 'antwortierte'."""
        docs = ROOT / "docs"
        found = []
        for path in docs.rglob("*.md"):
            text = path.read_text(encoding="utf-8")
            if "antwortierte" in text:
                found.append(str(path.relative_to(ROOT)))
        assert not found, f"Files still contain 'antwortierte': {found}"


    def test_no_raw_none_confidence_in_generated_pages(self):
        """No generated page must contain 'Konfidenz (raw): **None**' or 'Konfidenz (raw): None'."""
        docs = ROOT / "docs"
        found = []
        for path in docs.rglob("*.md"):
            text = path.read_text(encoding="utf-8")
            if "Konfidenz (raw): None" in text or "Konfidenz (raw): **None**" in text:
                found.append(str(path.relative_to(ROOT)))
        assert not found, f"Files contain raw None confidence: {found}"


if __name__ == "__main__":
    unittest.main()
