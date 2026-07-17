import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from build_index import Record, _card, recognition_summary


def rec(engine="kraken", model="m", page="p1", text="text", **extra):
    return {"engine": engine, "model_id": model, "page": page, "text": text, **extra}


class CatalogueSummaryTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
