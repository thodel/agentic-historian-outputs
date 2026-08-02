"""Committed withdrawal records and reproducible tombstone generation."""

from __future__ import annotations

import html
import json
import shutil
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

WITHDRAWALS = Path("data/withdrawals.json")
REQUIRED_FIELDS = {
    "status", "withdrawal_date", "reason", "decision_reference", "replacement",
}


def load_withdrawals(path: Path = WITHDRAWALS) -> dict[str, dict]:
    """Load and validate the committed withdrawal source of truth."""
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("withdrawals.json must contain an object keyed by document id")
    for doc_id, record in data.items():
        if not isinstance(record, dict) or REQUIRED_FIELDS - record.keys():
            missing = sorted(REQUIRED_FIELDS - record.keys()) if isinstance(record, dict) else sorted(REQUIRED_FIELDS)
            raise ValueError(f"withdrawal {doc_id!r} is missing fields: {', '.join(missing)}")
        if record["status"] != "withdrawn":
            raise ValueError(f"withdrawal {doc_id!r} must have status 'withdrawn'")
        date.fromisoformat(str(record["withdrawal_date"]))
        if not str(record["reason"]).strip():
            raise ValueError(f"withdrawal {doc_id!r} must give a public reason")
        decision = urlparse(str(record["decision_reference"]))
        if decision.scheme not in {"http", "https"} or not decision.netloc:
            raise ValueError(f"withdrawal {doc_id!r} needs a public decision URL")
    return data


def tombstone_page(doc_id: str, record: dict) -> str:
    """Render a minimal public notice without withdrawn research artifacts."""
    replacement = record.get("replacement")
    replacement_html = (
        f'<p>Replacement: <a href="{html.escape(str(replacement), quote=True)}">'
        f'{html.escape(str(replacement))}</a></p>'
        if replacement else "<p>No replacement is available.</p>"
    )
    return f'''---
layout: default
title: "Withdrawn output: {html.escape(doc_id)}"
robots: noindex
---

<nav class="breadcrumbs" aria-label="Breadcrumb"><a href="../">All outputs</a> <span aria-hidden="true">/</span> {html.escape(doc_id)}</nav>
<main class="withdrawal-notice" data-status="withdrawn">
  <p class="output-kicker">Withdrawn output</p>
  <h1>{html.escape(doc_id)}</h1>
  <p><strong>This output has been withdrawn and must not be cited as a current research output.</strong></p>
  <dl>
    <dt>Withdrawal date</dt><dd><time datetime="{html.escape(str(record['withdrawal_date']), quote=True)}">{html.escape(str(record['withdrawal_date']))}</time></dd>
    <dt>Reason</dt><dd>{html.escape(str(record['reason']))}</dd>
    <dt>Decision</dt><dd><a href="{html.escape(str(record['decision_reference']), quote=True)}">Public decision record</a></dd>
  </dl>
  {replacement_html}
  <p>The previously published material remains available only through the repository's Git history for auditability.</p>
</main>
'''


def build_tombstones(docs: Path, withdrawals: dict[str, dict]) -> None:
    """Replace each withdrawn live directory with its generated tombstone."""
    for doc_id, record in withdrawals.items():
        directory = docs / doc_id
        directory.mkdir(parents=True, exist_ok=True)
        for child in directory.iterdir():
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()
        (directory / "index.md").write_text(
            tombstone_page(doc_id, record), encoding="utf-8"
        )


def remove_withdrawn_entity_pages(root: Path, withdrawn_ids: set[str]) -> None:
    """Remove orphan entity pages whose only source was a withdrawn output."""
    if not root.exists():
        return
    for directory in root.iterdir():
        page = directory / "index.md"
        if not directory.is_dir() or not page.exists():
            continue
        content = page.read_text(encoding="utf-8")
        if any(f'../../{doc_id}/' in content for doc_id in withdrawn_ids):
            shutil.rmtree(directory)
