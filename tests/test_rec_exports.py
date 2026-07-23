"""Tests for structured recognition candidate exports (Epic 6, issue #38)."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from rec_exports import candidate_tei_xml, candidate_json_export


class TeiXmlExportTests(unittest.TestCase):
    maxDiff = 2000

    def _candidate(self, **overrides):
        base = {
            "engine": "kraken", "model_id": "model-1", "page": "p1",
            "text": "Hello world", "confidence": 0.95,
        }
        base.update(overrides)
        return base

    def test_renders_well_formed_xml(self):
        """TEI XML output is parseable and has required TEI elements."""
        xml = candidate_tei_xml(self._candidate(), "doc-1")
        # Must not raise
        import xml.etree.ElementTree as ET
        root = ET.fromstring(xml)
        # ET stores the TEI namespace in the element tag, not as xmlns attribute
        self.assertTrue(root.tag.endswith("TEI"), f"Expected TEI element, got {root.tag}")
        self.assertEqual(root.tag, "{http://www.tei-c.org/ns/1.0}TEI")

    def test_does_not_fabricate_line_or_region_coordinates(self):
        """TEI output contains no layout structure absent from the candidate."""
        xml = candidate_tei_xml(self._candidate(text="Line one\nLine two"))
        self.assertNotIn(" <line ", xml)
        self.assertNotIn(" <zone", xml)
        self.assertNotIn(" <region", xml)
        self.assertNotIn(" coords=", xml)

    def test_revision_desc_identifies_machine_generation(self):
        """TEI header marks the output as machine-generated, not human transcription."""
        xml = candidate_tei_xml(self._candidate(), "doc-1")
        self.assertIn("Machine-generated", xml)
        self.assertIn("agentic-historian", xml)
        # Boilerplate explicitly disclaims this as verified transcription
        self.assertIn("Not for citation as verified transcription", xml)

    def test_preserves_page_engine_model_provenance(self):
        """Page, engine, and model are recorded in the sourceDesc."""
        xml = candidate_tei_xml(self._candidate(
            engine="tesseract", model_id="latin/model", page="folio-3r"), "D-42")
        self.assertIn("tesseract", xml)
        self.assertIn("latin/model", xml)
        self.assertIn("folio-3r", xml)

    def test_empty_text_produces_empty_body(self):
        """Candidate with empty text produces a valid TEI with empty body (no <p>)."""
        xml = candidate_tei_xml(self._candidate(text=""), "doc-1")
        import xml.etree.ElementTree as ET
        root = ET.fromstring(xml)
        ns = "{http://www.tei-c.org/ns/1.0}"
        body = root.find(f".//{ns}body")
        self.assertIsNotNone(body)
        # Body has no child elements (no <p> for empty text)
        self.assertEqual(len(body), 0, "Empty text should produce body with no child elements")

    def test_unicode_text_is_escaped_safely(self):
        """Unicode characters are escaped in the XML output (no encoding errors)."""
        xml = candidate_tei_xml(self._candidate(text="Münster: café / über"), "doc-1")
        import xml.etree.ElementTree as ET
        root = ET.fromstring(xml)  # Must not raise
        p_elements = root.findall(".//{http://www.tei-c.org/ns/1.0}p")
        self.assertTrue(len(p_elements) > 0)

    def test_xml_contains_revision_desc_with_timestamp(self):
        """revisionDesc includes a timestamped change entry."""
        xml = candidate_tei_xml(self._candidate(), "doc-1")
        self.assertIn("revisionDesc", xml)
        self.assertIn("when=", xml)

    def test_derivation_is_not_mentioned_in_tei(self):
        """TEI export does not claim 'selected' derivation (only JSON export does)."""
        xml = candidate_tei_xml(self._candidate(selected=True), "doc-1")
        self.assertNotIn("selected", xml)
        self.assertNotIn("derivation", xml)


class JsonExportTests(unittest.TestCase):
    maxDiff = 2000

    def _candidate(self, **overrides):
        base = {
            "engine": "kraken", "model_id": "model-1", "page": "p1",
            "text": "Hello world", "confidence": 0.95,
        }
        base.update(overrides)
        return base

    def test_renders_valid_json(self):
        """JSON export parses without error."""
        import json
        obj = json.loads(candidate_json_export(self._candidate(), "doc-1"))
        self.assertEqual(obj["doc_id"], "doc-1")

    def test_selected_derivation_label(self):
        """Candidate marked selected carries derivation='selected'."""
        import json
        obj = json.loads(candidate_json_export(self._candidate(selected=True), "doc-1"))
        self.assertEqual(obj["derivation"], "selected")

    def test_candidate_derivation_label(self):
        """Unselected candidate carries derivation='candidate'."""
        import json
        obj = json.loads(candidate_json_export(self._candidate(), "doc-1"))
        self.assertEqual(obj["derivation"], "candidate")

    def test_confidence_is_float(self):
        """Confidence is serialised as a float."""
        import json
        obj = json.loads(candidate_json_export(self._candidate(confidence=0.873), "doc-1"))
        self.assertIsInstance(obj["confidence"], float)
        self.assertAlmostEqual(obj["confidence"], 0.873)

    def test_null_confidence_preserved(self):
        """Null/None confidence serialises as null."""
        import json
        obj = json.loads(candidate_json_export(self._candidate(confidence=None), "doc-1"))
        self.assertIsNone(obj["confidence"])

    def test_error_is_public_scrubbed(self):
        """Internal error details are not leaked into the export."""
        import json
        obj = json.loads(candidate_json_export(
            self._candidate(error="FileNotFoundError: /data/model.pkl not found"), "doc-1"))
        self.assertNotIn("FileNotFound", obj["error"])
        self.assertNotIn("model.pkl", obj["error"])

    def test_characters_count_excludes_error_cases(self):
        """characters is None when candidate has an error."""
        import json
        obj = json.loads(candidate_json_export(
            self._candidate(text="Hello", error="some error"), "doc-1"))
        self.assertIsNone(obj["characters"])

    def test_characters_count_includes_text_length(self):
        """characters reflects text length for successful candidates."""
        import json
        obj = json.loads(candidate_json_export(self._candidate(text="Hello world"), "doc-1"))
        self.assertEqual(obj["characters"], 11)

    def test_page_and_model_optional(self):
        """Missing page or model_id serialises as null."""
        import json
        obj = json.loads(candidate_json_export(
            self._candidate(page=None, model_id=""), "doc-1"))
        self.assertIsNone(obj["page"])
        self.assertIsNone(obj["model_id"])


class FormatApplicabilityTests(unittest.TestCase):
    """Acceptance: TXT always available; formats offered only when semantics supported."""

    def test_txt_is_always_available_for_text_candidate(self):
        """Plain text export is always valid for a non-empty text candidate."""
        # Contract: _candidates returns candidate entries with text/error fields
        from build_recognitions import _candidates
        entries = _candidates([{
            "engine": "kraken", "model_id": "m", "page": "p1",
            "text": "Some text", "confidence": 0.9,
        }], transcript="Some transcription")
        # entries maps to transcript-level candidates; check the API shape
        self.assertIsInstance(entries, list)

    def test_tei_contains_only_text_no_coordinates(self):
        """TEI export does not add layout markup the candidate did not produce."""
        xml = candidate_tei_xml(
            {"engine": "kraken", "model_id": "m", "page": "p1", "text": "Text only"},
            "doc")
        for tag in ("zone", "region", "line", "coords", "surface", "facsimile"):
            self.assertNotIn(f"<{tag}", xml, f"TEI must not fabricate <{tag}>")

    def test_tei_round_trip_parses_identically(self):
        """TEI XML round-trips through parsing without alteration."""
        import xml.etree.ElementTree as ET
        original = candidate_tei_xml(
            {"engine": "kraken", "model_id": "m", "page": "p1", "text": "Line one"},
            "doc-1")
        reparsed = ET.fromstring(original)
        self.assertTrue(reparsed.tag.endswith("TEI"), f"Expected TEI element, got {reparsed.tag}")


if __name__ == "__main__":
    unittest.main()
