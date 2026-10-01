#!/usr/bin/env python3
"""Does a published document's transcription hold any text at all?

Nothing asked that question before this file. ``detect_degeneration`` exists
and is good, but it runs over *candidates* — the individual engine outputs
inside a recognition (``build_index.py``, ``build_outputs.py``,
``build_recognitions.py``). A document with no recognitions at all therefore
has nothing for it to inspect, and its published transcription reaches the
site unexamined.

That is how ``u-17`` came to be published. Its transcription is 451 alphabetic
characters drawn from four distinct letters — 371 "u", 77 "i", 2 "s", 1 "g" —
it carries no recognitions, and it scores ``qa_score: 0.8``. It is also the
only document on the site with a mapped facsimile, so the one manuscript image
a reader can open sits beside that text.

The same shape appears three more times, and in each case the id cleanup in
#195 is what exposed it: ``0cf46c4`` moved the ``supersedes`` pointer from the
malformed id to the clean one without moving the content. Before it,
``u-17__`` (12,655 characters, 39 recognitions) superseded ``u-17`` (930
characters, none); after it, the stub is canonical and the substantive record
is the retired one. ``kf``/``kf-`` are the same swap over two records whose
transcriptions are byte-identical.

So this reports per published document, and deliberately exits zero. What to
*do* about a document that is already published — withdraw it, tombstone it,
re-run it, or invert the lineage back — is an editorial decision about the
publication, not something a build step may take. The accompanying test pins
the findings to a known set, so a new one fails CI while these wait for that
decision.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from quality import alphabet_profile, detect_degeneration  # noqa: E402

WITHDRAWALS_FILE = Path("data/withdrawals.json")

#: ``--- <image>.jpg ---`` separates the pages inside a joined transcription.
PAGE_MARKER = re.compile(r"^--- (\S+?\.(?:jpg|jpeg|png|jp2|tif)) ---$", re.M)

#: Each kind of finding, and what it means for a reader of the site.
KINDS = {
    "degenerate": "published transcription is engine noise, not text",
    "no_text": "pages are listed but no text was transcribed",
    "unaudited": "a transcription with no recognition behind it",
    "duplicate_pages": "another document transcribes the same images",
}


def _withdrawn(path: Path = WITHDRAWALS_FILE) -> set[str]:
    if not path.exists():
        return set()
    try:
        return set(json.loads(path.read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError):
        return set()


def page_ids(transcription: str) -> list[str]:
    """The image ids a joined transcription names, in order."""
    return PAGE_MARKER.findall(transcription or "")


def body_text(transcription: str) -> str:
    """The transcription with its page markers removed."""
    return PAGE_MARKER.sub("", transcription or "").strip()


def findings(docs_root: Path) -> list[dict]:
    """One row per problem found, ordered by document then kind."""
    withdrawn = _withdrawn()
    records: dict[str, dict] = {}

    for pipeline in sorted(docs_root.glob("*/pipeline.json")):
        doc_id = pipeline.parent.name
        if doc_id in withdrawn:
            continue
        try:
            data = json.loads(pipeline.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        transcription = data.get("transcription") or ""
        records[doc_id] = {
            "pages": page_ids(transcription),
            "body": body_text(transcription),
            "recognitions": len(data.get("recognitions") or []),
            "supersedes": data.get("supersedes"),
        }

    rows: list[dict] = []
    for doc_id, record in records.items():
        body = record["body"]
        alpha, distinct, top_share = alphabet_profile(body)

        if not body:
            rows.append({
                "doc_id": doc_id, "kind": "no_text",
                "detail": f"{len(record['pages'])} pages listed, no text",
            })
        else:
            degenerate, reason = detect_degeneration(body)
            if degenerate:
                rows.append({
                    "doc_id": doc_id, "kind": "degenerate",
                    "detail": (
                        f"{reason}; {alpha} alphabetic characters, "
                        f"{distinct} distinct, commonest {top_share:.0%}"
                    ),
                })
            if record["recognitions"] == 0:
                rows.append({
                    "doc_id": doc_id, "kind": "unaudited",
                    "detail": (
                        f"{alpha} alphabetic characters published with no "
                        "recognition recorded"
                    ),
                })

        pages = set(record["pages"])
        if not pages:
            continue
        for other_id, other in records.items():
            if other_id == doc_id:
                continue
            other_pages = set(other["pages"])
            if not other_pages or not pages <= other_pages:
                continue
            relation = "the same as" if pages == other_pages else "a subset of"
            rows.append({
                "doc_id": doc_id, "kind": "duplicate_pages",
                "detail": (
                    f"its {len(pages)} pages are {relation} "
                    f"{other_id}'s {len(other_pages)}"
                ),
            })

    rows.sort(key=lambda row: (row["doc_id"], row["kind"], row["detail"]))
    return rows


def summarize(rows: list[dict]) -> str:
    """A short human report, for CI output and for a release check."""
    if not rows:
        return "Transcription integrity: no findings."

    lines = [f"Transcription integrity: {len(rows)} findings.", ""]
    width = max(len(row["doc_id"]) for row in rows)
    for kind, meaning in KINDS.items():
        hits = [row for row in rows if row["kind"] == kind]
        if not hits:
            continue
        lines.append(f"{kind} — {meaning}")
        for row in hits:
            lines.append(f"  {row['doc_id']:<{width}}  {row['detail']}")
        lines.append("")
    lines.append(
        "Reported, not enforced: what to do with an already-published "
        "document is an editorial decision. See docs/source-backfill.md."
    )
    return "\n".join(lines)


def main() -> int:
    from build_outputs import DOCS

    print(summarize(findings(DOCS)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
