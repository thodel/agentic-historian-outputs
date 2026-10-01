"""Verified source references, held apart from the machine record (#182).

A source reference answers "which original is this a transcription of". That
is an editorial claim: somebody looked at a facsimile, matched it against the
text, and took responsibility for saying they correspond. It is not something
a recognition run knows.

Keeping it in ``pipeline.json`` therefore had two problems. A replacement run
that omitted ``source_url`` silently dropped the verification — the page went
from checkable to unverifiable with no record that anything had been lost. And
the record could not say *who* checked, *when*, or *against what*, so a
reference carried no more authority than a guess.

Verified references live here instead, in ``data/source-references.json``,
keyed by document id and committed like every other editorial registry
(withdrawals, editorial reviews). A machine re-run cannot touch them, and each
one names its institution, shelfmark, rights and verifier.

``pipeline.json`` may still carry a ``source_url``. It stays an *unverified*
hint from the pipeline and is presented as one; this ledger overrides it.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

LEDGER_FILE = Path("data/source-references.json")

#: Fields a verified reference must carry. Institution and shelfmark are what
#: make a reference checkable by someone who cannot reach the URL — a link
#: rots, a shelfmark does not.
REQUIRED = ("institution", "shelfmark", "rights", "verified_by", "verified_at")


def load_source_ledger(path: Path = LEDGER_FILE) -> dict[str, dict]:
    """Load and validate the committed verified-source records."""
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("version") != 1 or not isinstance(payload.get("documents"), dict):
        raise ValueError(
            "source-references.json must use version 1 and a documents object"
        )
    records = payload["documents"]
    for doc_id, record in records.items():
        if not isinstance(record, dict):
            raise ValueError(f"verified source for {doc_id!r} must be an object")
        missing = [field for field in REQUIRED
                   if not str(record.get(field, "")).strip()]
        if missing:
            raise ValueError(
                f"verified source for {doc_id!r} is missing: {', '.join(missing)}"
            )
        try:
            date.fromisoformat(str(record["verified_at"]))
        except ValueError as exc:
            raise ValueError(
                f"verified source for {doc_id!r}: verified_at must be YYYY-MM-DD"
            ) from exc
        if not (record.get("source_url") or record.get("iiif_manifest")):
            raise ValueError(
                f"verified source for {doc_id!r} needs a source_url or an "
                "iiif_manifest — a reference nobody can open is not a reference"
            )
    return records


def apply_source_ledger(data: dict, doc_id: str,
                        ledger: dict[str, dict] | None = None) -> tuple[dict, bool]:
    """Overlay the verified reference for *doc_id* onto a pipeline record.

    Returns the record and whether a verified reference was applied. The
    pipeline's own ``source_url`` is left in place when no verified record
    exists, so an unverified hint is still shown — as a hint.
    """
    records = load_source_ledger() if ledger is None else ledger
    record = records.get(doc_id)
    if not record:
        return data, False
    enriched = dict(data)
    for key in ("source_url", "iiif_manifest", "source_pages", "source_label",
                "source_attribution", "source_rights"):
        if record.get(key) is not None:
            enriched[key] = record[key]
    if record.get("rights") and not enriched.get("source_rights"):
        enriched["source_rights"] = record["rights"]
    enriched["source_verification"] = {
        "institution": record["institution"],
        "shelfmark": record["shelfmark"],
        "rights": record["rights"],
        "verified_by": record["verified_by"],
        "verified_at": str(record["verified_at"]),
        "note": str(record.get("note") or ""),
    }
    return enriched, True


def coverage(docs_root: Path, ledger: dict[str, dict] | None = None) -> list[dict]:
    """One row per published document: what can be checked, and how.

    This is the report #182 needs to close against. Its exit condition is not
    "every document has a link" — some originals are genuinely unavailable —
    but "every document has either a verified reference or a recorded reason".
    """
    from build_outputs import entities  # noqa: F401  (kept for import symmetry)
    from source_references import normalize_source_reference

    records = load_source_ledger() if ledger is None else ledger
    rows = []
    for pipeline in sorted(docs_root.glob("*/pipeline.json")):
        doc_id = pipeline.parent.name
        try:
            data = json.loads(pipeline.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            data = {}
        merged, verified = apply_source_ledger(data, doc_id, records)
        reference = normalize_source_reference(merged)
        record = records.get(doc_id, {})
        rows.append({
            "doc_id": doc_id,
            "verified": verified,
            "type": reference["type"],
            "mapped_pages": len(reference["pages"]),
            "institution": record.get("institution", ""),
            "shelfmark": record.get("shelfmark", ""),
            "unavailable_reason": str(record.get("unavailable_reason") or ""),
        })
    return rows


def summarize(rows: list[dict]) -> str:
    """A short human report, for CI output and for a release check."""
    total = len(rows)
    verified = sum(row["verified"] for row in rows)
    embeddable = sum(row["mapped_pages"] > 0 for row in rows)
    missing = [row["doc_id"] for row in rows
               if not row["verified"] and not row["unavailable_reason"]]
    lines = [
        f"Source coverage: {verified}/{total} verified, "
        f"{embeddable}/{total} with a mapped facsimile",
    ]
    if missing:
        lines.append(
            f"{len(missing)} document(s) with neither a verified reference nor "
            f"a recorded reason: {', '.join(sorted(missing))}"
        )
    else:
        lines.append("Every document has a verified reference or a recorded reason.")
    return "\n".join(lines)


def main() -> int:
    from build_outputs import DOCS

    rows = coverage(DOCS)
    print(summarize(rows))
    print()
    header = f'{"document":24} {"verified":9} {"type":14} {"pages":>5}  institution'
    print(header)
    print("-" * len(header))
    for row in rows:
        print(
            f'{row["doc_id"][:24]:24} {"yes" if row["verified"] else "no":9} '
            f'{row["type"][:14]:14} {row["mapped_pages"]:>5}  '
            f'{row["institution"] or row["unavailable_reason"] or "—"}'
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
