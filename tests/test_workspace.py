import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from build_outputs import evidence_workspace
from build_recognitions import build_recognition_section


class WorkspaceTests(unittest.TestCase):
    def test_image_source_creates_two_labelled_panes_and_separator(self):
        markup = evidence_workspace(
            {"source_url": "https://archive.org/page.jpg"}, "doc", "text", "")
        self.assertIn("data-evidence-workspace", markup)
        self.assertIn('role="region" aria-labelledby="source-heading"', markup)
        self.assertIn('role="region" aria-labelledby="transcription-heading"', markup)
        self.assertIn('role="separator"', markup)
        self.assertIn('aria-valuemin="25"', markup)
        self.assertIn('aria-valuemax="75"', markup)
        self.assertIn('tabindex="0" data-workspace-divider', markup)

    def test_iiif_source_creates_workspace(self):
        markup = evidence_workspace(
            {"iiif_manifest": "https://iiif.archive.org/item/manifest"},
            "doc", "text", "",
        )
        self.assertIn("data-evidence-workspace", markup)

    def test_landing_page_and_missing_source_preserve_linear_layout(self):
        for data in ({}, {"source_url": "https://archive.org/item/1"}):
            with self.subTest(data=data):
                markup = evidence_workspace(data, "doc", "text", "")
                self.assertNotIn("data-evidence-workspace", markup)
                self.assertIn('id="source"', markup)
                self.assertIn('id="transcription"', markup)

    def test_workspace_keeps_recognition_markup_in_transcription_pane(self):
        recognition = build_recognition_section(
            [{"engine": "kraken", "model_id": "m", "text": "candidate"}],
            "doc", "selected",
        )
        markup = evidence_workspace(
            {"source_url": "https://archive.org/page.jpg"},
            "doc", "selected", recognition,
        )
        transcription_pane = markup.split("evidence-pane--transcription", 1)[1]
        self.assertIn('id="transcription"', transcription_pane)
        self.assertIn('id="recognitions"', transcription_pane)


if __name__ == "__main__":
    unittest.main()
