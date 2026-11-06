"""Issue #778 — the evidence of a computed statement about the hand, on the page.

A document whose folder carries ``hand_consistency.json`` (the all-against-all
measurement of #773, with the hypothesis of #777) shows the distance matrix as a
heatmap, the centrality per page as a curve with the outliers marked, and the
outliers with a link to the facsimile where the source lists the page. A
document without the file shows nothing of it. Static SVG, no script, same
offline rule as the rest of the page.
"""

import json
import re
import sys
import tempfile
import unittest
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from build_outputs import build_document, hand_consistency_section  # noqa: E402

PAGES = [f"page-{i:04d}.jpg" for i in range(6)]
MATRIX = [[0.0 if i == j else (0.4 if (i < 4) == (j < 4) else 1.6) for j in range(6)] for i in range(6)]
REPORT = {
    "pages": PAGES, "matrix": MATRIX,
    "centrality": [0.6, 0.6, 0.6, 2.1, 0.9, 0.9],
    "typical": "page-0000.jpg", "outliers": ["page-0003.jpg"], "outlier_threshold": 1.7,
    "blocks": [], "changepoint": {"index": 4, "page": "page-0004.jpg", "ratio": 1.62},
    "silhouette2": 0.31, "skipped": [],
    "hint": {"wert": "Schriftbild ändert sich ab page-0004.jpg (Trennmass 1.62, Silhouette 0.31); "
                     "page-0003.jpg weicht stark ab. Mögliche neue Hand oder Schreibkampagne. Nicht geprüft.",
             "unsicher": True, "quelle": "berechnet"},
}
DATA = {
    "doc_id": "band-1",
    "transcription": "Item ein Text.",
    "source_url": "https://www.e-codices.unifr.ch/en/list/one/csg/0001",
    "source_pages": [
        {"page": "3", "canvas_url": "https://www.e-codices.unifr.ch/metadata/iiif/csg-0001/canvas/csg-0001_003.json"},
        {"page": "4", "canvas_url": "https://www.e-codices.unifr.ch/metadata/iiif/csg-0001/canvas/csg-0001_004.json"},
    ],
    "entities": [],
}


def _render(data, report=None, doc_id="band-1") -> str:
    with tempfile.TemporaryDirectory() as tmp:
        directory = Path(tmp) / doc_id
        directory.mkdir()
        (directory / "pipeline.json").write_text(json.dumps(data), encoding="utf-8")
        if report is not None:
            (directory / "hand_consistency.json").write_text(json.dumps(report), encoding="utf-8")
        build_document(directory / "pipeline.json", defaultdict(list))
        return (directory / "index.md").read_text(encoding="utf-8")


class HandConsistencyView(unittest.TestCase):

    def test_a_document_with_data_shows_matrix_curve_outliers_and_the_hypothesis(self):
        page = _render(DATA, REPORT)
        self.assertIn('id="hand"', page)
        self.assertIn('data-page-section="hand"', page)
        self.assertIn('<svg class="hand-matrix"', page)
        matrix = page.split('<svg class="hand-matrix"')[1].split('</svg>')[0]
        self.assertEqual(matrix.count('<rect x='), 36)                     # 6 × 6 cells
        self.assertEqual(matrix.count('hand-matrix__outlier'), 2)          # row and column mark
        self.assertIn('<svg class="hand-curve"', page)
        self.assertIn('<polyline class="hand-curve__line"', page)
        self.assertEqual(page.count('<circle class="hand-curve__outlier"'), 1)
        self.assertIn('class="hand-curve__split"', page)
        self.assertIn("Berechnete Hypothese:", page)
        self.assertIn("Schriftbild ändert sich ab page-0004.jpg", page)
        self.assertIn("quelle: berechnet, unsicher", page)
        # the outlier links to the facsimile the source lists for page 3
        self.assertIn('href="https://www.e-codices.unifr.ch/metadata/iiif/csg-0001/canvas/csg-0001_003.json">page-0003.jpg</a>', page)
        self.assertIn('<a href="hand_consistency.json">', page)
        # offline: nothing but inline SVG — no external image or script for it
        self.assertNotIn('<img', page.split('id="hand"')[1].split('</details>')[0])
        self.assertIn("6 Seiten, 1 Ausreisser, Hypothese", page)

    def test_a_document_without_data_shows_nothing_of_it(self):
        page = _render(DATA, None)
        self.assertNotIn('id="hand"', page)
        self.assertNotIn("hand-matrix", page)
        self.assertNotIn("Schriftbild entlang des Bandes", page)

    def test_a_report_without_a_hypothesis_says_so_and_links_no_facsimile_it_lacks(self):
        report = {**REPORT, "hint": None, "outliers": ["page-0005.jpg"]}
        page = _render(DATA, report)
        self.assertIn("Keine Hypothese", page)
        self.assertNotIn("Berechnete Hypothese", page)
        self.assertIn("<li>page-0005.jpg</li>", page)                  # page 5 has no source canvas
        self.assertIn("6 Seiten, 1 Ausreisser</span>", page)

    def test_a_broken_or_thin_report_is_ignored(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            (d / "hand_consistency.json").write_text("{not json", encoding="utf-8")
            self.assertEqual(hand_consistency_section(d, DATA), ("", 0))
            (d / "hand_consistency.json").write_text(json.dumps({"pages": ["a"], "matrix": [[0]]}), encoding="utf-8")
            self.assertEqual(hand_consistency_section(d, DATA), ("", 0))

    def test_the_heatmap_is_darker_where_pages_are_farther(self):
        section, n = hand_consistency_section_from(REPORT)
        self.assertEqual(n, 1)
        cells = re.findall(r'fill="rgb\((\d+),\d+,\d+\)"><title>page-0000.jpg × (page-00\d+.jpg): ([\d.]+)', section)
        shade = {page: int(grey) for grey, page, _d in cells}
        self.assertLess(shade["page-0004.jpg"], shade["page-0001.jpg"])   # 1.6 apart is darker than 0.4


def hand_consistency_section_from(report):
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        (d / "hand_consistency.json").write_text(json.dumps(report), encoding="utf-8")
        return hand_consistency_section(d, DATA)


if __name__ == "__main__":
    unittest.main()
