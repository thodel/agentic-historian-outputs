import json
import socket
import sys
import tempfile
import unittest
from collections import defaultdict
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import build_outputs
import reconcile_entities


def occurrence(label="Thun", confidence="high"):
    return {
        "label": label, "surface": label, "type": "PLACE", "context": "bei Thun",
        "confidence": confidence, "uri": "", "source_degenerate": False,
        "doc_id": "doc-a",
    }


class OfflineReconciliationRenderingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.original = (
            build_outputs.DOCS,
            build_outputs.RECONCILIATION_DATA,
            build_outputs.RECONCILIATION_REVIEW,
        )
        build_outputs.DOCS = root / "docs"
        build_outputs.DOCS.mkdir()
        build_outputs.RECONCILIATION_DATA = root / "candidates.json"
        build_outputs.RECONCILIATION_REVIEW = root / "review.json"
        build_outputs.RECONCILIATION_DATA.write_text(json.dumps({
            "candidates": {
                "PLACE:thun": {
                    "qid": "Q68978", "label": "Thun",
                    "description": "municipality in Switzerland",
                }
            }
        }))
        build_outputs.RECONCILIATION_REVIEW.write_text('{"suppress": []}')

    def tearDown(self):
        (
            build_outputs.DOCS,
            build_outputs.RECONCILIATION_DATA,
            build_outputs.RECONCILIATION_REVIEW,
        ) = self.original
        self.temp.cleanup()

    def render(self):
        item = occurrence()
        index = defaultdict(list, {
            build_outputs.entity_key("PLACE", "Thun"): [item]
        })
        build_outputs.build_entity_pages(index)
        return next((build_outputs.DOCS / "entities").glob("thun-*/index.md")).read_text()

    def test_candidate_is_explicitly_unverified(self):
        markup = self.render()
        self.assertIn("Unverifiziert — automatisch vorgeschlagen.", markup)
        self.assertIn("https://www.wikidata.org/entity/Q68978", markup)

    def test_static_build_does_not_use_network(self):
        with patch.object(socket, "create_connection", side_effect=AssertionError):
            self.assertIn("Q68978", self.render())

    def test_review_file_suppresses_false_candidate(self):
        build_outputs.RECONCILIATION_REVIEW.write_text(
            '{"suppress": ["PLACE:thun"]}'
        )
        markup = self.render()
        self.assertNotIn("Q68978", markup)
        self.assertIn("Nicht mit einem externen Normdatensatz", markup)


class BatchLookupTests(unittest.TestCase):
    def test_only_high_confidence_non_noise_entities_are_eligible(self):
        with tempfile.TemporaryDirectory() as tmp:
            docs = Path(tmp)
            directory = docs / "sample"
            directory.mkdir()
            (directory / "pipeline.json").write_text(json.dumps({
                "entities": {"entities": [
                    {"text": "Thun", "type": "PLACE", "hub_confidence": "high"},
                    {"text": "52", "type": "DATE", "hub_confidence": "high"},
                    {"text": "Baden", "type": "PLACE", "hub_confidence": "unverified"},
                ]}
            }))
            self.assertEqual(
                reconcile_entities.eligible_entities(docs),
                [("PLACE", "Thun")],
            )


if __name__ == "__main__":
    unittest.main()
