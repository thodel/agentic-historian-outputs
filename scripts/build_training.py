#!/usr/bin/env python3
"""Build ``docs/training/index.md`` — the training run catalogue.

Each run has a ``docs/training/<run_id>/training.json`` (produced by
serving-atr-inference after a training run completes).  This builder
aggregates all of them into a single browsable index.

A run belongs to its **datasets**, not to a document: it consumes 1..n
HuggingFace datasets and produces a model. The index therefore names the
datasets a run was trained on, and is keyed by ``run_id``.

Called by ``build_index.py`` after ``build_outputs()``.
"""

from __future__ import annotations

import json
import textwrap
from datetime import datetime, timezone
from pathlib import Path

from training_contract import (
    ContractError,
    TrainingContract,
    training_json_paths,
    validate_all_training_jsons,
)

DOCS = Path("docs")
TRAINING_INDEX = DOCS / "training" / "index.md"


def _format_duration(created: datetime, finished: datetime | None) -> str:
    if finished is None:
        return "—"
    delta = finished - created
    total_sec = int(delta.total_seconds())
    if total_sec < 60:
        return f"{total_sec}s"
    if total_sec < 3600:
        return f"{total_sec // 60}m {total_sec % 60}s"
    hours = total_sec // 3600
    minutes = (total_sec % 3600) // 60
    return f"{hours}h {minutes}m"


def _status_label(status: str) -> tuple[str, str]:
    """Return (badge_text, badge_modifier) for a training status."""
    return {
        "completed": ("Abgeschlossen", "ok"),
        "failed":    ("Fehlgeschlagen", "error"),
        "cancelled": ("Abgebrochen",   "warn"),
    }.get(status, (status, ""))


def _engine_label(engine: str) -> str:
    return {"kraken": "Kraken", "trocr": "TrOCR", "vllm": "VLM"}.get(engine, engine)


def _dataset_cell(datasets: list[dict]) -> str:
    """Render the datasets a run consumed, linked to the hub.

    Always a list: one dataset is the common case, several is a first-class one —
    a model trained on two corpora is a different model, and a cell that named
    only the first would misdescribe it.
    """
    if not datasets:
        return "—"
    parts = []
    for ds in datasets:
        repo = ds.get("hf_repo", "?")
        projects = ds.get("train_projects") or []
        suffix = f" ({len(projects)} Projekte)" if len(projects) > 1 else ""
        parts.append(
            f'<a href="https://huggingface.co/datasets/{repo}">{repo}</a>{suffix}'
        )
    return "<br>".join(parts)


def _build_rows(training_jsons: list[Path]) -> list[dict]:
    """Parse training.json files and return sorted row dicts for rendering."""
    rows: list[dict] = []
    for tpath in sorted(training_jsons):
        run_dir = tpath.parent.name
        try:
            data = json.loads(tpath.read_text(encoding="utf-8"))
            contract = TrainingContract(data)
        except (OSError, json.JSONDecodeError, ContractError) as exc:
            rows.append({
                "run_id": run_dir, "datasets_cell": "—", "status": "parse-error",
                "status_label": "Fehler", "status_mod": "error",
                "engine": "—", "model_id": "—",
                "epochs": "—", "epochs_trained": "—",
                "duration": "—", "cer": "—", "wer": "—",
                "error": str(exc)[:120],
            })
            continue

        label, mod = _status_label(contract.status)
        metrics = contract.metrics or {}
        cer = metrics.get("cer")
        wer = metrics.get("wer")
        rows.append({
            "datasets_cell": _dataset_cell(contract.datasets),
            "status": contract.status,
            "status_label": label,
            "status_mod": mod,
            "engine": _engine_label(contract.engine),
            "engine_raw": contract.engine,
            "model_id": contract.model_id,
            "epochs": contract.epochs,
            "epochs_trained": contract.epochs_trained,
            "duration": _format_duration(contract.created_at, contract.finished_at),
            "cer": f"{cer:.4f}" if cer is not None else "—",
            "wer": f"{wer:.4f}" if wer is not None else "—",
            "created_at": contract.created_at,
            "base_model": contract.base_model,
            "run_id": contract.run_id,
            "error": None,
        })
    # Sort: completed first (newest first), then failed, cancelled, parse errors last
    status_order = {"completed": 0, "failed": 1, "cancelled": 2, "parse-error": 3}
    rows.sort(key=lambda r: (status_order.get(r["status"], 99), r.get("created_at") or ""))
    return rows


def _render_table(rows: list[dict]) -> str:
    header = textwrap.dedent("""\
        <table class="training-table">
          <thead>
            <tr>
              <th scope="col">Datensätze</th>
              <th scope="col">Status</th>
              <th scope="col">Engine</th>
              <th scope="col">Modell</th>
              <th scope="col" class="num">Epochen</th>
              <th scope="col" class="num">Dauer</th>
              <th scope="col" class="num">CER</th>
              <th scope="col" class="num">WER</th>
            </tr>
          </thead>
          <tbody>
    """)
    body_parts: list[str] = []
    for r in rows:
        if r["status"] == "parse-error":
            body_parts.append(
                '<tr class="training-table__row training-table__row--error">'
                f'<td>{r["datasets_cell"]}</td>'
                '<td><span class="catalogue-badge catalogue-badge--error">Fehler</span></td>'
                f'<td colspan="5"><code>{r["error"]}</code></td>'
                '</tr>'
            )
            continue
        cer_display = r["cer"]
        wer_display = r["wer"]
        epoch_display = f'{r["epochs_trained"]}/{r["epochs"]}'
        body_parts.append(
            '<tr class="training-table__row training-table__row--' + r["status"] + '">'
            f'<td>{r["datasets_cell"]}</td>'
            f'<td><span class="catalogue-badge catalogue-badge--{r["status_mod"]}">{r["status_label"]}</span></td>'
            f'<td>{r["engine"]}</td>'
            f'<td><code>{r["model_id"]}</code></td>'
            f'<td class="num">{epoch_display}</td>'
            f'<td class="num">{r["duration"]}</td>'
            f'<td class="num">{cer_display}</td>'
            f'<td class="num">{wer_display}</td>'
            '</tr>'
        )
    body = "".join(body_parts)
    footer = "          </tbody>\n        </table>"
    return header + body + footer


def _render_summary(rows: list[dict]) -> str:
    total = len(rows)
    completed = sum(1 for r in rows if r["status"] == "completed")
    failed = sum(1 for r in rows if r["status"] == "failed")
    cancelled = sum(1 for r in rows if r["status"] == "cancelled")
    errors = sum(1 for r in rows if r["status"] == "parse-error")
    completed_cers = []
    for r in rows:
        if r["status"] == "completed" and r["cer"] not in ("—", None):
            try:
                completed_cers.append(float(r["cer"]))
            except ValueError:
                pass
    best_cer = f"{min(completed_cers):.4f}" if completed_cers else "—"
    runs_word = "Lauf" if total == 1 else "Läufe"
    lines = [f"- **Gesamt:** {total} Training {runs_word}"]
    if completed:
        lines.append(f"  - Abgeschlossen: {completed}")
    if failed:
        lines.append(f"  - Fehlgeschlagen: {failed}")
    if cancelled:
        lines.append(f"  - Abgebrochen: {cancelled}")
    if errors:
        lines.append(f"  - Lesefehler: {errors}")
    if best_cer != "—" and completed:
        lines.append(f"- **Beste CER** (abgeschlossene Läufe): {best_cer}")
    return "\n".join(lines)


def build_training() -> int:
    """Find all ``docs/*/training.json`` and write ``docs/training/index.md``.

    Returns the number of training runs found (including errors).
    """
    training_jsons = training_json_paths(DOCS)
    if not training_jsons:
        TRAINING_INDEX.parent.mkdir(parents=True, exist_ok=True)
        TRAINING_INDEX.write_text(
            "---\ntitle: Training\n---\n\n"
            "Bisher keine Training-Läufe vorhanden.\n",
            encoding="utf-8",
        )
        print("build_training: no training.json files found, wrote empty index")
        return 0

    rows = _build_rows(training_jsons)
    table = _render_table(rows)
    summary = _render_summary(rows)

    page = f"""---
title: Training
---

# Training

Training runs produced by [serving-atr-inference](https://github.com/thodel/serving-atr-inference).

## Zusammenfassung

{summary}

## Training runs

{table}

<style>
.training-table {{ border-collapse: collapse; width: 100%; font-size: 0.875rem; }}
.training-table th, .training-table td {{ padding: 0.4rem 0.6rem; border: 1px solid var(--border, #ccc); text-align: left; }}
.training-table th {{ background: var(--surface-alt, #f5f5f5); font-weight: 600; }}
.training-table .num {{ text-align: right; font-variant-numeric: tabular-nums; }}
.training-table__row--completed {{ background: var(--row-ok, #f0faf0); }}
.training-table__row--failed    {{ background: var(--row-error, #fdf0f0); }}
.training-table__row--cancelled {{ background: var(--row-warn, #fdfaf0); }}
.training-table__row--parse-error {{ background: var(--row-error, #f0f0f0); }}
</style>
"""
    TRAINING_INDEX.parent.mkdir(parents=True, exist_ok=True)
    TRAINING_INDEX.write_text(page, encoding="utf-8")
    print(f"build_training: wrote {len(rows)} training run(s) to {TRAINING_INDEX}")
    return len(rows)


if __name__ == "__main__":
    build_training()
