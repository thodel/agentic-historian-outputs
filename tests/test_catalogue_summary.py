import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from build_index import (
    CATALOGUE_PERFORMANCE_BUDGETS, Record, RecognitionSummary, _card,
    recognition_summary,
)
from datetime import datetime, timezone


def rec(engine="kraken", model="m", page="p1", text="text", **extra):
    return {"engine": engine, "model_id": model, "page": page, "text": text, **extra}


class CatalogueSummaryTests(unittest.TestCase):
    def card(self, summary):
        return _card(Record(
            "very-long-document-identifier", datetime.now(timezone.utc), "", "Latin", "Gothic",
            "Letter", 0, 1, None, 0, False, "preview", summary.review_status,
            recognition_summary=summary,
        ))

    def test_current_counts_are_typed_and_deterministic(self):
        data = {"recognitions": [
            rec(), rec("vlm", "v", text=""),
            rec("trocr", "t", error="timeout"),
            rec("kraken", "deg", text="x " * 6000),
        ]}
        summary = recognition_summary(data)
        self.assertEqual(summary.provenance, "current")
        self.assertEqual(
            (summary.total, summary.successful, summary.failed, summary.empty, summary.degenerate),
            (4, 1, 1, 1, 1),
        )

    def test_duplicate_records_do_not_inflate_engine_or_model_counts(self):
        summary = recognition_summary({"recognitions": [rec(), rec(), rec("Kraken", "m")]})
        self.assertEqual(summary.engines, ("kraken",))
        self.assertEqual(summary.model_count, 1)
        self.assertEqual(summary.total, 3)

    def test_comparison_requires_two_usable_candidates_on_same_known_page(self):
        same = recognition_summary({"recognitions": [rec(model="a"), rec(model="b")]})
        split = recognition_summary({"recognitions": [rec(model="a", page="p1"), rec(model="b", page="p2")]})
        unknown_multi = recognition_summary({
            "a_meta": {"pages": 2},
            "recognitions": [rec(model="a", page=""), rec(model="b", page="")],
        })
        self.assertTrue(same.comparison_ready)
        self.assertFalse(split.comparison_ready)
        self.assertFalse(unknown_multi.comparison_ready)
        self.assertEqual(same.comparison_pair, ("p1-kraken-a", "p1-kraken-b", "p1"))

    def test_page_source_and_review_fields_are_derived(self):
        summary = recognition_summary({
            "review_status": "human-verified",
            "source_url": "https://archive.org/image.jpg",
            "source_pages": [{"page": "p1", "image_url": "https://archive.org/1.jpg"}],
            "recognitions": [rec()],
        })
        self.assertEqual(summary.page_count, 1)
        self.assertTrue(summary.source_available)
        self.assertEqual(summary.source_type, "image")
        self.assertEqual(summary.review_status, "human-verified")

    def test_legacy_output_is_honest_not_zero_or_clean(self):
        summary = recognition_summary({"transcription": "legacy text"})
        self.assertEqual(summary.provenance, "legacy")
        self.assertIsNone(summary.total)
        self.assertFalse(summary.comparison_ready)

    def test_summary_size_is_independent_of_transcript_length(self):
        short = recognition_summary({"transcription": "x", "recognitions": [rec(text="short")]})
        long = recognition_summary({"transcription": "x" * 1_000_000, "recognitions": [rec(text="short")]})
        self.assertEqual(json.dumps(short.as_dict()), json.dumps(long.as_dict()))
        self.assertLess(len(json.dumps(long.as_dict())), 600)

    def test_compact_payload_and_card_stay_within_budgets(self):
        summary = recognition_summary({"recognitions": [
            rec("kraken", "a"), rec("trocr", "b", error="timeout"),
        ]})
        payload = json.dumps(summary.as_dict(), ensure_ascii=False,
                             separators=(",", ":"))
        card = self.card(summary)
        self.assertLessEqual(len(payload.encode()),
                             CATALOGUE_PERFORMANCE_BUDGETS["summary_bytes_per_record"])
        self.assertLessEqual(len(card.encode()),
                             CATALOGUE_PERFORMANCE_BUDGETS["card_bytes_per_record"])
        self.assertNotIn("recognitions", payload)
        self.assertNotIn("candidate text", payload)

    def test_no_javascript_primary_link_is_always_present(self):
        summary = recognition_summary({"recognitions": [rec()]})
        card = self.card(summary)
        self.assertIn('<h2><a href="very-long-document-identifier/">', card)
        self.assertIn('class="catalogue-actions"', card)

    def test_human_title_is_primary_and_identifier_is_secondary(self):
        summary = recognition_summary({"recognitions": [rec()]})
        record = Record(
            "bat-664", datetime.now(timezone.utc), "1429", "de", "Kurrent",
            "Urbar", 0, 1, 0.75, 0, False, "preview", "machine-generated",
            recognition_summary=summary,
            display_title="Urbar · 1429",
            shelfmark="BAT 664, Blatt 27r",
        )
        card = _card(record)
        self.assertIn('<h2><a href="bat-664/">Urbar · 1429</a></h2>', card)
        self.assertIn('Dokument-ID <code>bat-664</code>', card)
        self.assertNotIn("Legacy-QA", card)

    def test_card_exposes_accessible_engine_chips_and_candidate_counts(self):
        summary = recognition_summary({"recognitions": [rec("kraken", "a"), rec("trocr", "b")]})
        card = self.card(summary)
        self.assertIn('aria-label="Erkennungsprovenienz"', card)
        self.assertIn('Erkennungsengine: </span>kraken', card)
        self.assertIn('2 erfolgreich / 2 insgesamt', card)
        self.assertIn('<details class="catalogue-details">', card)
        self.assertIn('<dl class="catalogue-summary-facts">', card)

    def test_card_surfaces_failures_missing_source_and_legacy_provenance(self):
        current = recognition_summary({"recognitions": [rec(), rec("vlm", "v", error="timeout")]})
        card = self.card(current)
        self.assertIn("1 fehlgeschlagener Erkennungsversuch", card)
        self.assertIn("Keine digitale Quelle", card)
        legacy = RecognitionSummary("legacy", None, None, None, None, None, (), 0, None,
                                    False, "missing", "machine-generated", False)
        self.assertIn("Begrenzte Provenienz", self.card(legacy))

    def test_document_is_always_primary_and_capabilities_are_secondary(self):
        compare = self.card(recognition_summary({"recognitions": [rec(model="a"), rec(model="b")]}))
        self.assertIn('class="catalogue-action catalogue-action--primary"', compare)
        self.assertIn('href="very-long-document-identifier/"', compare)
        self.assertIn("Dokument öffnen", compare)
        self.assertIn('class="catalogue-action catalogue-action--secondary"', compare)
        self.assertIn("Modelle vergleichen", compare)
        self.assertIn("?cmp=p1-kraken-a:p1-kraken-b&amp;page=p1#recognitions", compare)
        inspect = self.card(recognition_summary({"recognitions": [rec()]}))
        self.assertIn("Erkennungen ansehen", inspect)
        self.assertIn("?rec=selected#recognition-selected", inspect)
        legacy = RecognitionSummary("legacy", None, None, None, None, None, (), 0, None,
                                    False, "missing", "machine-generated", False)
        legacy_card = self.card(legacy)
        self.assertIn("Dokument öffnen", legacy_card)
        self.assertNotIn("catalogue-action--secondary", legacy_card)
        self.assertEqual(legacy_card.count('class="catalogue-actions"'), 1)

    def test_source_visual_uses_thumbnail_or_explicit_placeholder(self):
        summary = recognition_summary({"recognitions": [rec()]})
        record = Record(
            "with-source", datetime.now(timezone.utc), "", "Latin", "Gothic",
            "Letter", 0, 1, None, 0, False, "preview", summary.review_status,
            recognition_summary=summary,
            source_thumbnail_url="https://archive.org/folio.jpg",
        )
        card = _card(record)
        self.assertIn('class="catalogue-source-visual catalogue-source-visual--image"', card)
        self.assertIn('src="https://archive.org/folio.jpg"', card)
        self.assertIn('loading="lazy"', card)

        missing = self.card(summary)
        self.assertIn('catalogue-source-visual--missing', missing)
        self.assertIn("Quelle fehlt", missing)


if __name__ == "__main__":
    unittest.main()
