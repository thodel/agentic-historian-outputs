import tempfile
import unittest
from pathlib import Path

from build_outputs import recognition_candidates, recognition_viewer


class RecognitionViewerTests(unittest.TestCase):
    def test_normalizes_selected_success_and_failure(self):
        data = {"transcription": "fused", "recognitions": [
            {"engine": "vlm", "model_id": "v1", "text": "alpha", "confidence": .8},
            {"engine": "trocr", "model_id": "t1", "text": "", "error": "timeout"},
        ]}
        candidates = recognition_candidates(data)
        self.assertEqual([c["id"] for c in candidates], ["selected", "vlm-v1", "trocr-t1"])
        self.assertTrue(candidates[0]["selected"])
        self.assertEqual(candidates[2]["error"], "timeout")

    def test_duplicate_candidate_ids_are_unique(self):
        data = {"recognitions": [
            {"engine": "kraken", "model_id": "same", "text": "a"},
            {"engine": "kraken", "model_id": "same", "text": "b"},
        ]}
        ids = [c["id"] for c in recognition_candidates(data)]
        self.assertEqual(len(ids), len(set(ids)))

    def test_viewer_exposes_all_candidates_and_errors(self):
        data = {"transcription": "fused", "recognitions": [
            {"engine": "vlm", "model_id": "v1", "text": "alpha", "confidence": .8},
            {"engine": "trocr", "model_id": "t1", "error": "service timeout"},
        ]}
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "recognitions").mkdir()
            (root / "recognitions" / "fused.txt").write_text("fused")
            rendered = recognition_viewer(data, root)
        self.assertIn("Ausgewählt / Fusion", rendered)
        self.assertIn("vlm · v1", rendered)
        self.assertIn("service timeout", rendered)
        self.assertIn("Engine-Konfidenz", rendered)

    def test_legacy_output_keeps_plain_transcription(self):
        with tempfile.TemporaryDirectory() as tmp:
            rendered = recognition_viewer({"transcription": "legacy"}, Path(tmp))
        self.assertIn('<pre class="transcription"', rendered)
        self.assertNotIn("recognition-selector", rendered)


if __name__ == "__main__":
    unittest.main()
