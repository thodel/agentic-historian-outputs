#!/usr/bin/env python3
"""Build a docs tree with a small synthetic corpus, for the styled-site suite.

Five of the integration tests assert things about a document card: that one is
visible without scrolling, that an absent source renders smaller than a real
facsimile, that the catalogue is navigable without JavaScript, that a
document's citable downloads resolve. They ran against whatever happened to be
published, so when every output was withdrawn (#254) all five failed at once —
not because the site broke, but because the suite had been quietly depending on
the corpus being non-empty.

Skipping them was not an option: this suite fails rather than skips, on the
principle that a test which quietly does not run is worse than one that fails.
So they get a corpus of their own. Two documents, because the pair is what the
facsimile test compares: one with a mapped page image, one with no source at
all.

Everything else — the theme, the stylesheets, the static pages, the config — is
the real ``docs/`` tree, so the fixture site is the same site with two
documents in it.

Usage:
    python3 tests/fixtures/styled_fixture.py [destination]

Prints the destination path. ``scripts/build_styled_fixture.sh`` runs this and
then Jekyll over the result.
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

#: Copied from the real tree; anything else is generated or is a document.
KEEP_FILES = {"_config.yml", "about.md", "methodology.md", "forschung.md",
              "evaluation.md", "vlm-finetuning.md", "catalogue-verification.md",
              "catalogue-performance.md", "source-backfill.md"}
KEEP_DIRS = {"assets", "_includes", "training", "tests"}

PAGE = "e-codices_saa-0428_015v_large.jpg"


def _document(doc_id: str, *, with_source: bool) -> dict:
    """One synthetic record. Real enough for the theme to render a full card."""
    record: dict = {
        "doc_id": doc_id,
        "transcription": (
            f"--- {PAGE} ---\n"
            "Wir Johans von Habspurg tuon kunt allen den die disen brief "
            "ansehent oder hoerent lesen daz wir mit gutem willen und "
            "wolbedahtem muote gegeben haben dem closter ze Koenigsfelden "
            "zehen schillinge geltes jaerlicher guelte von unserm hofe."
        ),
        "description": {
            "source_description": f"Synthetische Urkunde {doc_id}.",
            "source_json": {"Datierung": "1357", "Sprache": "Deutsch",
                            "Schrift": "Gotische Kurrentschrift",
                            "Inhalt": "Urkunde"},
        },
        "entities": [
            {"name": "Johans von Habspurg", "type": "PERSON",
             "context": "Aussteller", "confidence": "high"},
            {"name": "Königsfelden", "type": "PLACE",
             "context": "Empfänger", "confidence": "high"},
        ],
        "errors": [],
        "a_meta": {"pages": 1, "qa_score": 0.8},
        # Three, not one. The behavioural suite needs at least two candidates
        # for the compare pane to open and for recognition selection to have
        # something to switch between, and a failed one so the viewer renders
        # its error state too.
        "recognitions": [
            {"engine": "vlm", "model_id": "internvl3-8b-instruct", "page": PAGE,
             "text": "Wir Johans von Habspurg tuon kunt allen den die disen "
                     "brief ansehent oder hoerent lesen daz wir mit gutem "
                     "willen gegeben haben dem closter ze Koenigsfelden.",
             "confidence": 0.81, "error": None},
            {"engine": "kraken", "model_id": "kraken-catmus-medieval",
             "page": PAGE,
             "text": "Wir Johans von Habspurg tuon kunt allen den die disen "
                     "brief ansehnt oder horent lesen daz wir mit gutem "
                     "willen gegeben haben dem closter ze Konigsfelden.",
             "confidence": 0.74, "error": None},
            {"engine": "trocr", "model_id": "trocr-kurrent-xvi-xvii",
             "page": PAGE, "text": "", "confidence": None,
             "error": "Der Erkennungsdienst war nicht erreichbar.",
             "status_code": "unavailable"},
        ],
    }
    if with_source:
        record |= {
            "source_url": "https://www.e-codices.unifr.ch/en/saa/0428",
            "source_label": "e-codices: Staatsarchiv Aargau, SAA 428",
            "source_attribution": "Staatsarchiv Aargau / e-codices",
            "source_rights": "See the rights statement on e-codices",
            "source_pages": [{
                "page": PAGE,
                "canvas_url": "https://www.e-codices.unifr.ch/en/saa/0428/15v",
                "image_url": "https://www.e-codices.unifr.ch/loris/saa/"
                             "saa-0428/saa-0428_015v.jp2/full/1200,/0/default.jpg",
            }],
        }
    return record


def build(destination: Path) -> Path:
    import build_index
    import build_outputs

    if destination.exists():
        shutil.rmtree(destination)
    docs = destination / "docs"
    docs.mkdir(parents=True)

    source = ROOT / "docs"
    for name in KEEP_DIRS:
        if (source / name).is_dir():
            shutil.copytree(source / name, docs / name)
    for name in KEEP_FILES:
        if (source / name).is_file():
            shutil.copy2(source / name, docs / name)

    for doc_id, with_source in (("fixture-mit-quelle", True),
                                ("fixture-ohne-quelle", False)):
        directory = docs / doc_id
        directory.mkdir()
        (directory / "pipeline.json").write_text(
            json.dumps(_document(doc_id, with_source=with_source),
                       ensure_ascii=False, indent=2),
            encoding="utf-8")

    originals = (build_index.DOCS, build_outputs.DOCS)
    build_index.DOCS = docs
    build_outputs.DOCS = docs
    try:
        build_outputs.build()
        build_index.build()
    finally:
        build_index.DOCS, build_outputs.DOCS = originals

    cards = (docs / "index.md").read_text(encoding="utf-8").count(
        'class="catalogue-card"')
    if cards != 2:
        raise SystemExit(
            f"fixture corpus rendered {cards} cards, expected 2 — the tests "
            "that depend on it would pass or fail for the wrong reason")
    return docs


if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "_styled-fixture-src"
    print(build(target))
