"""Document lineage: the ``supersedes`` relation between re-processed runs.

When a source is processed more than once, the newer run declares which older
document it replaces via a top-level ``supersedes`` key in ``pipeline.json``
(or ``a_meta.supersedes``).  The generators use this to link the two runs, put
a banner on each, de-emphasize superseded runs in the catalogue, and count
current versus superseded outputs separately (issue #125).

This module is shared by ``build_index.py`` (catalogue) and ``build_outputs.py``
(document pages) so the lineage graph is derived identically on both sides.
"""

from __future__ import annotations

import json
from pathlib import Path


def supersedes_target(data: dict) -> str:
    """Return the doc id this document declares it replaces, or "".

    Accepts the field at the top level or under ``a_meta``.
    """
    meta = data.get("a_meta") if isinstance(data.get("a_meta"), dict) else {}
    return str(data.get("supersedes") or meta.get("supersedes") or "").strip()


def build_lineage(docs_dir: Path) -> "tuple[dict[str, str], dict[str, str]]":
    """Scan every ``pipeline.json`` and derive the lineage graph.

    Returns ``(supersedes, superseded_by)`` where:

    - ``supersedes[doc_id]`` is the older doc a run replaces (only when that
      predecessor actually exists as a published document);
    - ``superseded_by[old_id]`` is the newer doc that replaces it.  If several
      runs claim the same predecessor, the lexicographically greatest id wins
      so the mapping is deterministic.
    """
    existing: set[str] = set()
    declared: dict[str, str] = {}
    for path in sorted(docs_dir.glob("*/pipeline.json")):
        doc_id = path.parent.name
        existing.add(doc_id)
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        target = supersedes_target(data)
        if target and target != doc_id:
            declared[doc_id] = target

    # Keep only edges whose predecessor is a real published document; a run may
    # not point a public "replaced by" banner at a document that does not exist.
    supersedes = {doc: target for doc, target in declared.items() if target in existing}
    superseded_by: dict[str, str] = {}
    for doc, target in sorted(supersedes.items()):
        if target not in superseded_by or doc > superseded_by[target]:
            superseded_by[target] = doc
    return supersedes, superseded_by
