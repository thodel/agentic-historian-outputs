import json, tempfile, unittest
from pathlib import Path
from scripts.editorial_reviews import apply_review, load_reviews

class EditorialReviewTests(unittest.TestCase):
    def test_correction_preserves_machine_record(self):
        machine = {"transcription": "maschinell"}
        reviews = {"doc": {"status": "human-verified", "reviewer": "Ada", "reviewed_at": "2026-08-02", "correction": {"transcription": "korrigiert"}}}
        enriched, review = apply_review(machine, "doc", reviews)
        self.assertEqual((enriched["transcription"], enriched["review_status"]), ("korrigiert", "human-verified"))
        self.assertEqual(machine["transcription"], "maschinell")
        self.assertEqual(review["reviewer"], "Ada")

    def test_unattributed_review_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "reviews.json"
            path.write_text(json.dumps({"version": 1, "documents": {"doc": {"status": "human-verified", "reviewed_at": "yesterday"}}}), encoding="utf-8")
            with self.assertRaises(ValueError): load_reviews(path)
