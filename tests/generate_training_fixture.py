#!/usr/bin/env python3
"""Render a training run page into the browser-fixture directory.

The behavioural suite had fixtures for the catalogue and two documents and
none for a training run, so the whole training report — two SVGs, the
provenance notices, the disclosures, the exact table — was never opened in a
browser. Everything about it was asserted against strings in generated markup.

No run is published yet, and inventing one under ``docs/`` would put a
fabricated research record on the public site. The fixture is therefore built
from ``tests/fixtures/training_run_sample.json`` through the real renderer,
so what the browser sees is what the generator produces, not a hand-written
copy that drifts.

Run before ``node generate-fixtures.mjs``; the Node step copies the
stylesheets this page references.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from build_training import _run_page  # noqa: E402
from training_contract import TrainingContract  # noqa: E402

RECORD = ROOT / "tests" / "fixtures" / "training_run_sample.json"
OUTPUT = ROOT / "tests" / "behavioural" / "fixtures" / "training.html"


def render() -> str:
    contract = TrainingContract(json.loads(RECORD.read_text(encoding="utf-8")))
    page = _run_page({
        "contract": contract,
        "run_id": contract.run_id,
        "model_id": contract.model_id,
        "status": contract.status,
        "status_mod": "ok",
        "status_label": "Abgeschlossen",
        "recognition_usages": [
            {"doc_id": "u-17", "candidate_id": "p1-kraken-medieval",
             "engine": "kraken", "page": "1", "failed": False},
            {"doc_id": "koenige", "candidate_id": "p2-kraken-medieval",
             "engine": "kraken", "page": "2", "failed": True},
        ],
    })
    # Same transformation generate-fixtures.mjs applies: drop the front matter
    # and resolve Jekyll's relative_url filter to a plain path.
    body = re.sub(r"^---\n.*?\n---\n", "", page, count=1, flags=re.S)
    body = re.sub(
        r"\{\{\{?\s*'/assets/([^']+)'\s*\|\s*relative_url\s*\}\}\}?",
        r"/assets/\1", body,
    )
    return (
        "<!DOCTYPE html>\n<html lang=\"de\">\n<head><meta charset=\"UTF-8\">"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">"
        "<title>Test Fixture</title></head>\n"
        f"<body>{body}</body>\n</html>\n"
    )


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(render(), encoding="utf-8")
    print(f"Generated training fixture: {OUTPUT}")


if __name__ == "__main__":
    main()
