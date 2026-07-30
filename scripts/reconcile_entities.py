#!/usr/bin/env python3
"""Batch Wikidata candidate lookup for credible, high-confidence entities.

This command is deliberately separate from the static-site build.  It is the
only entity-reconciliation component that uses the network; its JSON output is
reviewed and committed before the offline build consumes it.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).parent))

from build_outputs import (  # noqa: E402
    DOCS, entities, entity_display_label, entity_is_uncertain, entity_key,
    reconciliation_key,
)

API = "https://www.wikidata.org/w/api.php"


def eligible_entities(docs: Path = DOCS) -> list[tuple[str, str]]:
    index = defaultdict(list)
    for path in sorted(docs.glob("*/pipeline.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        for item in entities(data):
            index[entity_key(item["type"], item["label"])].append(item)
    eligible = []
    for (kind, _), occurrences in sorted(index.items()):
        label = entity_display_label(occurrences)
        high_confidence = any(
            item["confidence"].casefold() in {"high", "verified"}
            for item in occurrences
        )
        if high_confidence and not entity_is_uncertain(occurrences[0], len(occurrences)):
            eligible.append((kind, label))
    return eligible


def search_wikidata(query: str, timeout: float = 20.0) -> dict | None:
    params = urlencode({
        "action": "wbsearchentities", "format": "json", "language": "de",
        "uselang": "de", "limit": 1, "search": query,
    })
    request = Request(f"{API}?{params}", headers={
        "User-Agent": "agentic-historian-outputs reconciliation/1.0"
    })
    with urlopen(request, timeout=timeout) as response:
        payload = json.load(response)
    result = next(iter(payload.get("search", [])), None)
    if not isinstance(result, dict):
        return None
    return {
        "qid": str(result.get("id", "")),
        "label": str(result.get("label", "")),
        "description": str(result.get("description", "")),
        "query": query,
        "status": "unverified-automatic-suggestion",
    }


def build_candidates(docs: Path = DOCS) -> dict:
    candidates = {}
    for kind, label in eligible_entities(docs):
        candidate = search_wikidata(label)
        if candidate:
            candidates[reconciliation_key(kind, label)] = candidate
    return {
        "schema_version": 1,
        "generated_at": date.today().isoformat(),
        "generator": "scripts/reconcile_entities.py",
        "candidates": candidates,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output", type=Path, default=Path("data/entity-reconciliation.json")
    )
    parser.add_argument("--docs", type=Path, default=DOCS)
    args = parser.parse_args()
    payload = build_candidates(args.docs)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {len(payload['candidates'])} candidates to {args.output}")


if __name__ == "__main__":
    main()
