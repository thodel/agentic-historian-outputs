"""The training page carries an authored comparison above the runs.

`docs/training/index.md` is generated: every build rewrites it from the
published `training.json` files, and with none published it said only that
there was nothing yet. The comparison of Kraken, TrOCR and the fine-tuned
vision-language models on the same data is written by hand, so it lives in
`docs/training/_uebersicht.md` (a leading underscore: Jekyll does not publish
it as a page of its own) and the builder puts it into the index — with and
without runs, so a rebuild never overwrites it. The smaller lessons sit on a
sub-page of their own, `einsichten.md`.
"""

from __future__ import annotations

import json
import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tests"))

from build_training import OVERVIEW_NAME, build_training  # noqa: E402
from test_training_reports import valid_case  # noqa: E402

DOCS = ROOT / "docs"
OVERVIEW = "## Auf einen Blick\n\nKraken, TrOCR und VLMs auf denselben Daten.\n"


def _build(docs: Path, *, runs: int, overview: str | None) -> str:
    training = docs / "training"
    training.mkdir(parents=True, exist_ok=True)
    if overview is not None:
        (training / OVERVIEW_NAME).write_text(overview, encoding="utf-8")
    if runs:
        run = training / valid_case()["run_id"]
        run.mkdir(parents=True)
        (run / "training.json").write_text(json.dumps(valid_case()), encoding="utf-8")
    target = training / "index.md"
    with patch("build_training.DOCS", docs), patch("build_training.TRAINING_INDEX", target):
        build_training()
    return target.read_text(encoding="utf-8")


class GeneratedIndexTests(unittest.TestCase):
    def test_the_overview_stands_above_an_empty_list(self):
        with tempfile.TemporaryDirectory() as temp:
            index = _build(Path(temp) / "docs", runs=0, overview=OVERVIEW)
        self.assertIn("Kraken, TrOCR und VLMs auf denselben Daten.", index)
        self.assertLess(index.index("## Auf einen Blick"), index.index("## Veröffentlichte Läufe"))
        self.assertIn("noch keine Trainingsläufe veröffentlicht", index)

    def test_the_overview_stands_above_the_runs(self):
        with tempfile.TemporaryDirectory() as temp:
            index = _build(Path(temp) / "docs", runs=1, overview=OVERVIEW)
        self.assertLess(index.index("## Auf einen Blick"), index.index("## Training runs"))
        self.assertIn("training-atr-models", index)
        self.assertNotIn("serving-atr-inference", index, "training moved out in September")

    def test_without_an_overview_the_index_still_builds(self):
        with tempfile.TemporaryDirectory() as temp:
            index = _build(Path(temp) / "docs", runs=0, overview=None)
        self.assertTrue(index.startswith("---\nlayout: default\ntitle: Training\n---"))
        self.assertIn("## Veröffentlichte Läufe", index)


class PublishedPagesTests(unittest.TestCase):
    def test_the_overview_is_not_a_page_of_its_own(self):
        self.assertTrue(OVERVIEW_NAME.startswith("_"), "Jekyll skips underscore files")
        text = (DOCS / "training" / OVERVIEW_NAME).read_text(encoding="utf-8")
        self.assertFalse(text.startswith("---"), "front matter would make it a page")

    def test_the_committed_index_carries_the_overview(self):
        overview = (DOCS / "training" / OVERVIEW_NAME).read_text(encoding="utf-8").strip()
        index = (DOCS / "training" / "index.md").read_text(encoding="utf-8")
        self.assertIn(overview, index, "run scripts/build_training.py after editing it")

    def test_the_comparison_covers_all_three_families(self):
        text = (DOCS / "training" / OVERVIEW_NAME).read_text(encoding="utf-8")
        for family in ("Kraken", "TrOCR", "VLM"):
            self.assertIn(family, text)
        self.assertIn("einsichten.html", text, "the lessons have their own page")

    def test_the_lessons_page_is_german_and_links_back(self):
        text = (DOCS / "training" / "einsichten.md").read_text(encoding="utf-8")
        self.assertRegex(text, r"(?m)^title: \"Training: Einsichten und Probleme im Ablauf\"$")
        self.assertIn("](./)", text, "a link back to the overview")
        self.assertNotIn("Internal engineering document", text)

    def test_relative_links_resolve(self):
        """Links from /training/ and /training/einsichten.html to site pages."""
        for name in (OVERVIEW_NAME, "einsichten.md"):
            text = (DOCS / "training" / name).read_text(encoding="utf-8")
            for target in re.findall(r"\]\((\.\./[^)#]+|[a-z][^):#]*\.html)", text):
                path = (DOCS / "training" / target).resolve()
                candidates = [path.with_suffix(".md"), path / "index.md", path]
                self.assertTrue(any(c.exists() for c in candidates), f"{name}: {target}")


if __name__ == "__main__":
    unittest.main()
