import json
import sys
import tempfile
import unittest
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import build_outputs


def entity(label, kind="PERSON", **extra):
    return {
        "label": label, "surface": label, "type": kind, "context": "",
        "confidence": "", "uri": "", "source_degenerate": False, **extra,
    }


class EntityNoiseScoreTests(unittest.TestCase):
    def test_current_digit_fixture_is_quarantined(self):
        score, reasons = build_outputs.entity_noise_score(entity("52", "DATE"), 1)
        self.assertGreaterEqual(score, 2)
        self.assertIn("nur Ziffern", reasons)

    def test_current_gibberish_fixtures_are_quarantined(self):
        for label in ("fiisdz", "gerrmreuon", "darnm"):
            with self.subTest(label=label):
                self.assertTrue(build_outputs.entity_is_uncertain(entity(label), 1))

    def test_repeated_credible_place_is_not_quarantined(self):
        self.assertFalse(build_outputs.entity_is_uncertain(entity("Thun", "PLACE"), 2))

    def test_explicit_degenerate_source_is_counted(self):
        score, reasons = build_outputs.entity_noise_score(
            entity("Enaben", "PLACE", source_degenerate=True), 3
        )
        self.assertGreaterEqual(score, 3)
        self.assertIn("degenerierter Quellkandidat", reasons)


class EntityTriageRenderingTests(unittest.TestCase):
    def setUp(self):
        self.original_docs = build_outputs.DOCS
        self.temp = tempfile.TemporaryDirectory()
        build_outputs.DOCS = Path(self.temp.name)

    def tearDown(self):
        build_outputs.DOCS = self.original_docs
        self.temp.cleanup()

    def test_index_groups_uncertain_entities_without_deleting_them(self):
        credible = {"doc_id": "a", **entity("Thun", "PLACE")}
        noisy = {"doc_id": "b", **entity("52", "DATE")}
        build_outputs.build_entity_pages(defaultdict(list, {
            ("PLACE", "Thun"): [credible, {**credible, "doc_id": "c"}],
            ("DATE", "52"): [noisy],
        }))
        page = (build_outputs.DOCS / "entities" / "index.md").read_text()
        self.assertIn("<h2>Glaubwürdige Erkennungen</h2>", page)
        self.assertIn("<summary>Unsichere Erkennungen (1)</summary>", page)
        self.assertIn(">52</a>", page)
        entity_page = next((build_outputs.DOCS / "entities").glob("52-*/index.md"))
        self.assertIn("Unsichere Erkennung.", entity_page.read_text())

    def test_document_page_surfaces_the_same_flag(self):
        directory = build_outputs.DOCS / "doc"
        directory.mkdir()
        pipeline = directory / "pipeline.json"
        pipeline.write_text(json.dumps({
            "transcription": "52",
            "entities": {"entities": [{"text": "52", "type": "DATE"}]},
        }))
        item = build_outputs.entities(json.loads(pipeline.read_text()))[0]
        index = defaultdict(list, {("DATE", "52"): [{"doc_id": "doc", **item}]})
        build_outputs.build_document(pipeline, index, collect_entities=False)
        self.assertIn("Unsichere Erkennung · Score", (directory / "index.md").read_text())


if __name__ == "__main__":
    unittest.main()
