#!/usr/bin/env python3
"""Build the static, accessible training-run catalogue.

Training runs are dataset-centric: each ``docs/training/<run_id>/training.json``
describes the datasets consumed and the model produced.  This module renders a
compact index plus self-contained reports for curves, provenance,
reproducibility, and scoped validation metrics.  It deliberately requires no
JavaScript or third-party plotting library.
"""

from __future__ import annotations

import html
import json
import math
import re
import textwrap
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

from quality import render_reference_evaluation, training_reference_evaluations
from training_contract import ContractError, CurveEpoch, TrainingContract, training_json_paths

DOCS = Path("docs")
TRAINING_INDEX = DOCS / "training" / "index.md"
_HF_REVISION = re.compile(r"^[A-Za-z0-9._-]{7,128}$")
_HF_MODEL = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*/[A-Za-z0-9][A-Za-z0-9._-]*$")


def _esc(value: object, *, attr: bool = False) -> str:
    return html.escape(str(value), quote=attr)


def _format_duration(created: datetime, finished: datetime | None) -> str:
    if finished is None:
        return "—"
    total_sec = max(0, int((finished - created).total_seconds()))
    if total_sec < 60:
        return f"{total_sec}s"
    if total_sec < 3600:
        return f"{total_sec // 60}m {total_sec % 60}s"
    return f"{total_sec // 3600}h {(total_sec % 3600) // 60}m"


def _status_label(status: str) -> tuple[str, str]:
    return {
        "completed": ("Abgeschlossen", "ok"),
        "failed": ("Fehlgeschlagen", "error"),
        "cancelled": ("Abgebrochen", "warn"),
    }.get(status, (status, ""))


def _engine_label(engine: str) -> str:
    return {"kraken": "Kraken", "trocr": "TrOCR", "vllm": "VLM"}.get(engine, engine)


def _dataset_url(dataset: dict, *, pinned: bool = False) -> str:
    repo = str(dataset.get("hf_repo") or "")
    base = f"https://huggingface.co/datasets/{quote(repo, safe='/')}"
    revision = str(dataset.get("revision") or "")
    if pinned and _HF_REVISION.fullmatch(revision):
        return f"{base}/tree/{quote(revision, safe='')}"
    return base


def _dataset_cell(datasets: list[dict]) -> str:
    parts = []
    for dataset in datasets:
        repo = str(dataset.get("hf_repo") or "?")
        projects = dataset.get("train_projects") or []
        suffix = f" ({len(projects)} Projekte)" if len(projects) > 1 else ""
        parts.append(
            f'<a href="{_esc(_dataset_url(dataset, pinned=True), attr=True)}" '
            f'rel="external">{_esc(repo)}</a>{suffix}'
        )
    return "<br>".join(parts) or "—"


def _build_rows(training_jsons: list[Path]) -> list[dict]:
    rows: list[dict] = []
    for tpath in sorted(training_jsons):
        run_dir = tpath.parent.name
        try:
            contract = TrainingContract(json.loads(tpath.read_text(encoding="utf-8")), tpath)
        except (OSError, json.JSONDecodeError, ContractError) as exc:
            rows.append({
                "run_id": run_dir,
                "datasets_cell": "—",
                "status": "parse-error",
                "status_label": "Fehler",
                "status_mod": "error",
                "engine": "—",
                "model_id": "—",
                "epochs": "—",
                "epochs_trained": "—",
                "duration": "—",
                "cer": "—",
                "wer": "—",
                "created_at": None,
                "error": str(exc)[:500],
                "contract": None,
            })
            continue

        label, modifier = _status_label(contract.status)
        metrics = contract.metrics or {}
        rows.append({
            "run_id": contract.run_id,
            "datasets_cell": _dataset_cell(contract.datasets),
            "status": contract.status,
            "status_label": label,
            "status_mod": modifier,
            "engine": _engine_label(contract.engine),
            "model_id": contract.model_id,
            "epochs": contract.epochs,
            "epochs_trained": contract.epochs_trained,
            "duration": _format_duration(contract.created_at, contract.finished_at),
            "cer": _format_error_rate(metrics.get("cer")),
            "wer": _format_error_rate(metrics.get("wer")),
            "created_at": contract.created_at,
            "error": None,
            "contract": contract,
        })
    status_order = {"completed": 0, "failed": 1, "cancelled": 2, "parse-error": 3}
    rows.sort(
        key=lambda row: (
            status_order.get(row["status"], 99),
            -(row["created_at"].timestamp()) if row["created_at"] else math.inf,
        )
    )
    return rows


def _format_error_rate(value: object) -> str:
    if value is None:
        return "—"
    return f"{float(value) * 100:.2f}%"


def _render_table(rows: list[dict]) -> str:
    header = textwrap.dedent("""\
        <div class="training-table-wrap" tabindex="0" role="region" aria-label="Übersicht der Trainingsläufe">
        <table class="training-table">
          <thead><tr>
            <th scope="col">Datensätze</th><th scope="col">Status</th>
            <th scope="col">Engine</th><th scope="col">Modell</th>
            <th scope="col" class="num">Epochen</th><th scope="col" class="num">Dauer</th>
            <th scope="col" class="num"><abbr title="Character Error Rate auf dem Validierungsdatensatz; niedriger ist besser">Validierungs-CER</abbr></th>
            <th scope="col" class="num"><abbr title="Word Error Rate auf dem Validierungsdatensatz; niedriger ist besser">Validierungs-WER</abbr></th>
          </tr></thead><tbody>
    """)
    body: list[str] = []
    for row in rows:
        if row["status"] == "parse-error":
            body.append(
                '<tr class="training-table__row training-table__row--error">'
                f'<td>—</td><td><span class="catalogue-badge catalogue-badge--error">Fehler</span></td>'
                f'<td colspan="6"><code>{_esc(row["error"])}</code></td></tr>'
            )
            continue
        run_id = _esc(row["run_id"], attr=True)
        body.append(
            f'<tr class="training-table__row training-table__row--{row["status"]}">'
            f'<td>{row["datasets_cell"]}</td>'
            f'<td><span class="catalogue-badge catalogue-badge--{row["status_mod"]}">{row["status_label"]}</span></td>'
            f'<td>{_esc(row["engine"])}</td>'
            f'<td><a href="#run-{run_id}"><code>{_esc(row["model_id"])}</code></a></td>'
            f'<td class="num">{row["epochs_trained"]}/{row["epochs"]}</td>'
            f'<td class="num">{row["duration"]}</td><td class="num">{row["cer"]}</td>'
            f'<td class="num">{row["wer"]}</td></tr>'
        )
    return header + "".join(body) + "</tbody></table></div>"


def _metric_points(curves: list[CurveEpoch], field: str) -> list[tuple[int, float]]:
    return [(curve.epoch, float(getattr(curve, field))) for curve in curves if getattr(curve, field) is not None]


def _polyline(points: list[tuple[int, float]], x_min: float, x_max: float,
              y_min: float, y_max: float) -> str:
    left, top, width, height = 62.0, 24.0, 620.0, 210.0
    x_span = x_max - x_min or 1.0
    y_span = y_max - y_min or 1.0
    return " ".join(
        f"{left + (x - x_min) / x_span * width:.1f},{top + height - (y - y_min) / y_span * height:.1f}"
        for x, y in points
    )


def _render_svg_chart(curves: list[CurveEpoch], run_id: str, chart: str) -> str:
    if chart == "loss":
        series = [("Trainingsverlust", "train_loss", "training-chart__train"),
                  ("Validierungsverlust", "val_loss", "training-chart__validation")]
        title = "Trainings- und Validierungsverlust nach Epoche"
        y_label = "Verlust"
    else:
        series = [("Validierungsgenauigkeit", "val_accuracy", "training-chart__accuracy")]
        title = "Validierungsgenauigkeit nach Epoche"
        y_label = "Genauigkeit (%)"
    available = [(label, css, _metric_points(curves, field)) for label, field, css in series]
    available = [item for item in available if item[2]]
    if not available:
        return ""
    all_points = [point for _, _, points in available for point in points]
    x_min, x_max = min(x for x, _ in all_points), max(x for x, _ in all_points)
    y_values = [y for _, y in all_points]
    y_min = 0.0 if min(y_values) >= 0 else min(y_values)
    y_max = max(y_values) or 1.0
    chart_id = re.sub(r"[^a-zA-Z0-9_-]", "-", f"{run_id}-{chart}")
    lines = []
    legend = []
    for label, css, points in available:
        lines.append(
            f'<polyline class="training-chart__line {css}" points="{_polyline(points, x_min, x_max, y_min, y_max)}" />'
        )
        legend.append(f'<li class="{css}"><span aria-hidden="true"></span>{label}</li>')
    grid = "".join(
        f'<line class="training-chart__grid" x1="62" y1="{24 + i * 52.5:.1f}" x2="682" y2="{24 + i * 52.5:.1f}" />'
        for i in range(5)
    )
    return (
        '<figure class="training-chart">'
        f'<svg viewBox="0 0 720 280" role="img" aria-labelledby="{chart_id}-title {chart_id}-desc">'
        f'<title id="{chart_id}-title">{title}</title>'
        f'<desc id="{chart_id}-desc">Epochen {x_min} bis {x_max}; Wertebereich {y_min:.3g} bis {y_max:.3g}. Die exakten Werte folgen als Tabelle.</desc>'
        f'{grid}<line class="training-chart__axis" x1="62" y1="234" x2="682" y2="234" />'
        '<line class="training-chart__axis" x1="62" y1="24" x2="62" y2="234" />'
        f'<text class="training-chart__label" x="372" y="270" text-anchor="middle">Epoche</text>'
        f'<text class="training-chart__label" x="16" y="130" text-anchor="middle" transform="rotate(-90 16 130)">{y_label}</text>'
        f'<text class="training-chart__tick" x="62" y="251" text-anchor="middle">{x_min:g}</text>'
        f'<text class="training-chart__tick" x="682" y="251" text-anchor="middle">{x_max:g}</text>'
        f'<text class="training-chart__tick" x="54" y="238" text-anchor="end">{y_min:.3g}</text>'
        f'<text class="training-chart__tick" x="54" y="29" text-anchor="end">{y_max:.3g}</text>'
        f'{"".join(lines)}</svg><figcaption>{title}</figcaption>'
        f'<ul class="training-chart__legend">{"".join(legend)}</ul></figure>'
    )


def _render_curve_table(curves: list[CurveEpoch]) -> str:
    rows = []
    for curve in curves:
        value = lambda field: "—" if getattr(curve, field) is None else f"{getattr(curve, field):.6g}"
        rows.append(
            f'<tr><th scope="row">{curve.epoch}</th><td>{value("train_loss")}</td>'
            f'<td>{value("val_loss")}</td><td>{value("val_accuracy")}</td><td>{value("lr")}</td></tr>'
        )
    return (
        '<details class="training-curve-data"><summary>Kurvendaten als Tabelle</summary>'
        '<div class="training-table-wrap" tabindex="0"><table><thead><tr><th scope="col">Epoche</th>'
        '<th scope="col">Trainingsverlust</th><th scope="col">Validierungsverlust</th>'
        '<th scope="col">Validierungsgenauigkeit (%)</th><th scope="col">Lernrate</th>'
        f'</tr></thead><tbody>{"".join(rows)}</tbody></table></div></details>'
    )


def _render_curves(contract: TrainingContract) -> str:
    if not contract.curves:
        return '<p class="training-empty">Für diesen Lauf wurden keine Kurvendaten veröffentlicht.</p>'
    charts = _render_svg_chart(contract.curves, contract.run_id, "loss")
    charts += _render_svg_chart(contract.curves, contract.run_id, "accuracy")
    return f'<div class="training-charts">{charts}</div>{_render_curve_table(contract.curves)}'


def _join_projects(values: object) -> str:
    return ", ".join(_esc(value) for value in values or []) or "Nicht angegeben"


def _render_dataset_panel(contract: TrainingContract) -> str:
    cards = []
    for index, dataset in enumerate(contract.datasets, start=1):
        repo = str(dataset["hf_repo"])
        revision = str(dataset.get("revision") or "")
        counts = []
        for key, label in (("pages", "Seiten"), ("lines", "Zeilen"),
                           ("chars", "Zeichen"), ("pages_skipped", "Übersprungene Seiten")):
            if dataset.get(key) is not None:
                counts.append(f'<div><dt>{label}</dt><dd>{int(dataset[key]):,}</dd></div>')
        revision_html = (
            f'<a href="{_esc(_dataset_url(dataset, pinned=True), attr=True)}"><code>{_esc(revision[:12])}</code></a>'
            if revision else "Nicht angegeben"
        )
        cards.append(
            '<article class="training-dataset">'
            f'<h5>Datensatz {index}: <a href="{_esc(_dataset_url(dataset), attr=True)}" rel="external">{_esc(repo)}</a></h5>'
            '<dl class="training-facts">'
            f'<div><dt>Revision</dt><dd>{revision_html}</dd></div>'
            f'<div><dt>Split</dt><dd>{_esc(dataset.get("split") or "Nicht angegeben")}</dd></div>'
            f'<div><dt>Trainingsprojekte</dt><dd>{_join_projects(dataset.get("train_projects"))}</dd></div>'
            f'<div><dt>Evaluationsprojekte</dt><dd>{_join_projects(dataset.get("eval_projects"))}</dd></div>'
            f'{"".join(counts)}</dl></article>'
        )
    return '<div class="training-datasets">' + "".join(cards) + "</div>"


def _format_param(value: object) -> str:
    if isinstance(value, bool):
        return "Ja" if value else "Nein"
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return str(value)


def _base_model_html(base_model: str | None) -> str:
    if not base_model:
        return "Nicht angegeben"
    if _HF_MODEL.fullmatch(base_model):
        url = f"https://huggingface.co/{quote(base_model, safe='/')}"
        return f'<a href="{_esc(url, attr=True)}" rel="external"><code>{_esc(base_model)}</code></a>'
    if re.fullmatch(r"10\.\d{4,9}/\S+", base_model):
        return f'<a href="https://doi.org/{_esc(quote(base_model, safe="/"), attr=True)}"><code>{_esc(base_model)}</code></a>'
    return f'<code>{_esc(base_model)}</code>'


def _render_reproducibility(contract: TrainingContract) -> str:
    params = "".join(
        f'<div><dt><code>{_esc(key)}</code></dt><dd><code>{_esc(_format_param(value))}</code></dd></div>'
        for key, value in sorted(contract.params.items())
    ) or '<div><dt>Parameter</dt><dd>Nicht veröffentlicht</dd></div>'
    finished = contract.finished_at.isoformat() if contract.finished_at else "Nicht angegeben"
    run_path = f'{quote(contract.run_id, safe="")}/training.json'
    return (
        '<dl class="training-facts training-model-card">'
        f'<div><dt>Erzeugtes Modell</dt><dd><code>{_esc(contract.model_id)}</code></dd></div>'
        f'<div><dt>Basismodell</dt><dd>{_base_model_html(contract.base_model)}</dd></div>'
        f'<div><dt>Engine</dt><dd>{_esc(_engine_label(contract.engine))} (<code>{_esc(contract.engine)}</code>)</dd></div>'
        f'<div><dt>Lauf-ID</dt><dd><code>{_esc(contract.run_id)}</code></dd></div>'
        f'<div><dt>Schema</dt><dd>training.json v{contract.schema_version}</dd></div>'
        f'<div><dt>Gestartet</dt><dd><time datetime="{_esc(contract.created_at.isoformat(), attr=True)}">{_esc(contract.created_at.isoformat())}</time></dd></div>'
        f'<div><dt>Beendet</dt><dd>{_esc(finished)}</dd></div>'
        f'<div><dt>Epochen</dt><dd>{contract.epochs_trained} von {contract.epochs}</dd></div>'
        f'<div><dt>Protokollpfad</dt><dd><code>{_esc(contract.log or "Nicht angegeben")}</code></dd></div>'
        f'</dl><h5>Hyperparameter</h5><dl class="training-facts training-params">{params}</dl>'
        f'<p><a href="{_esc(run_path, attr=True)}">Maschinenlesbares training.json öffnen</a></p>'
    )


def _evaluation_scope(contract: TrainingContract) -> str:
    scopes = []
    for dataset in contract.datasets:
        projects = dataset.get("eval_projects") or []
        if projects:
            scopes.extend(f'{dataset["hf_repo"]}: {project}' for project in projects)
    return "; ".join(scopes) or "Evaluationssplit nicht genauer dokumentiert"


def _render_metrics(contract: TrainingContract) -> str:
    metrics = contract.metrics or {}
    definitions = []
    supplementary_specs = (
        ("char_accuracy", "Zeichengenauigkeit", "percent", "higher", lambda v: f"{float(v):.2f}%"),
        ("word_accuracy", "Wortgenauigkeit", "percent", "higher", lambda v: f"{float(v):.2f}%"),
        ("chars", "Ausgewertete Zeichen", "count", "none", lambda v: f"{int(v):,}"),
        ("errors", "Zeichenfehler", "count", "lower", lambda v: f"{int(v):,}"),
    )
    scope = _evaluation_scope(contract)
    datasets = ",".join(dataset["hf_repo"] for dataset in contract.datasets)
    reference_blocks = []
    for provenance in training_reference_evaluations(
        metrics, contract.datasets, contract.params, contract.engine, contract.model_id
    ):
        key = provenance.unit.casefold()
        reference_blocks.append(
            render_reference_evaluation(
                provenance,
                suffix=f"training-{contract.run_id}-{key}",
                doc_id=contract.run_id,
                page_depth=1,
            )
        )
    for key, label, unit, direction, formatter in supplementary_specs:
        if metrics.get(key) is None:
            continue
        direction_text = {"lower": "Niedriger ist besser.", "higher": "Höher ist besser.", "none": ""}[direction]
        definitions.append(
            f'<div class="training-metric" data-quality-metric="{key}" data-unit="{unit}" '
            f'data-scope="validation-set" data-direction="{direction}" data-datasets="{_esc(datasets, attr=True)}">'
            f'<dt>{label}</dt><dd><strong>{formatter(metrics[key])}</strong>'
            f'<span>{direction_text}</span></dd></div>'
        )
    if not reference_blocks and not definitions:
        return '<p class="training-empty">Keine Validierungsmetriken veröffentlicht.</p>'
    supplementary = (
        f'<h5>Ergänzende Zähl- und Genauigkeitswerte</h5><dl class="training-metrics">{"".join(definitions)}</dl>'
        if definitions else ""
    )
    return (
        '<p class="training-metric-note">Diese Werte wurden auf den dokumentierten Evaluationsdaten berechnet. '
        'Sie sind nur zwischen Läufen mit demselben Datensatz, derselben Revision und demselben Evaluationssplit direkt vergleichbar.</p>'
        f'<p><strong>Geltungsbereich:</strong> {_esc(scope)}</p>'
        f'<div class="training-reference-metrics">{"".join(reference_blocks)}</div>{supplementary}'
    )


def _render_run_report(row: dict) -> str:
    contract: TrainingContract = row["contract"]
    run_id = _esc(contract.run_id, attr=True)
    return (
        f'<article class="training-run" id="run-{run_id}" data-training-run="{run_id}">'
        '<header class="training-run__header"><div>'
        f'<p class="training-run__kicker">{_esc(_engine_label(contract.engine))} · {_esc(contract.created_at.date())}</p>'
        f'<h3><code>{_esc(contract.model_id)}</code></h3></div>'
        f'<span class="catalogue-badge catalogue-badge--{row["status_mod"]}">{row["status_label"]}</span></header>'
        '<details open><summary>Trainingskurven</summary>'
        f'<div class="training-panel">{_render_curves(contract)}</div></details>'
        '<details><summary>Datensatzprovenienz</summary>'
        f'<div class="training-panel">{_render_dataset_panel(contract)}</div></details>'
        '<details><summary>Reproduzierbarkeit und Modellkarte</summary>'
        f'<div class="training-panel">{_render_reproducibility(contract)}</div></details>'
        '<details><summary>Validierungsmetriken</summary>'
        f'<div class="training-panel">{_render_metrics(contract)}</div></details></article>'
    )


def _render_summary(rows: list[dict]) -> str:
    total = len(rows)
    counts = {status: sum(row["status"] == status for row in rows)
              for status in ("completed", "failed", "cancelled", "parse-error")}
    lines = [f'- **Gesamt:** {total} Training {"Lauf" if total == 1 else "Läufe"}']
    for status, label in (("completed", "Abgeschlossen"), ("failed", "Fehlgeschlagen"),
                          ("cancelled", "Abgebrochen"), ("parse-error", "Lesefehler")):
        if counts[status]:
            lines.append(f'  - {label}: {counts[status]}')
    completed_rates = [float(row["contract"].metrics["cer"]) for row in rows
                       if row.get("contract") and row["status"] == "completed"
                       and row["contract"].metrics and row["contract"].metrics.get("cer") is not None]
    if completed_rates:
        lines.append(f'- **Niedrigste berichtete Validierungs-CER:** {min(completed_rates) * 100:.2f}%')
    return "\n".join(lines)


_STYLES = """
<style>
.training-table-wrap { overflow-x: auto; margin: 1rem 0; }
.training-table, .training-curve-data table { border-collapse: collapse; width: 100%; font-size: .875rem; }
.training-table th, .training-table td, .training-curve-data th, .training-curve-data td { padding: .45rem .6rem; border: 1px solid var(--catalogue-border, #ccd3da); text-align: left; }
.training-table th { background: #f3f6f8; font-weight: 700; }
.training-table .num { text-align: right; font-variant-numeric: tabular-nums; }
.training-run { margin: 1.5rem 0; border: 1px solid var(--catalogue-border, #ccd3da); border-radius: .8rem; overflow: hidden; }
.training-run__header { display: flex; justify-content: space-between; gap: 1rem; align-items: start; padding: 1rem; background: #f3f6f8; }
.training-run__header h3, .training-run__kicker { margin: 0; }
.training-run__kicker { color: #5c6875; font-size: .8rem; }
.training-run > details { border-top: 1px solid var(--catalogue-border, #ccd3da); }
.training-run > details > summary { padding: .75rem 1rem; cursor: pointer; color: #245b78; font-weight: 700; }
.training-run > details > summary:focus-visible { outline: 3px solid #f5b942; outline-offset: -3px; }
.training-panel { padding: 0 1rem 1rem; }
.training-charts { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 28rem), 1fr)); gap: 1rem; }
.training-chart { min-width: 0; margin: .75rem 0; }
.training-chart svg { display: block; width: 100%; height: auto; border: 1px solid #d7dee5; background: #fff; }
.training-chart__axis { stroke: #52606d; stroke-width: 1.5; }
.training-chart__grid { stroke: #d7dee5; stroke-width: 1; }
.training-chart__line { fill: none; stroke-width: 3; stroke-linecap: round; stroke-linejoin: round; }
.training-chart__train { stroke: #176b87; }
.training-chart__validation { stroke: #a44a12; stroke-dasharray: 8 5; }
.training-chart__accuracy { stroke: #3b7d44; }
.training-chart__label, .training-chart__tick { fill: #35414c; font-family: system-ui, sans-serif; font-size: 12px; }
.training-chart__legend { display: flex; flex-wrap: wrap; gap: .75rem; margin: .4rem 0; padding: 0; list-style: none; font-size: .82rem; }
.training-chart__legend span { display: inline-block; width: 1.7rem; margin-right: .3rem; border-top: 3px solid currentColor; vertical-align: middle; }
.training-chart__legend .training-chart__validation span { border-top-style: dashed; }
.training-facts, .training-metrics { display: grid; grid-template-columns: repeat(auto-fit, minmax(13rem, 1fr)); gap: .75rem; }
.training-facts div, .training-metric { min-width: 0; padding: .65rem; background: #f6f8f9; border-radius: .4rem; }
.training-facts dt, .training-metric dt { color: #5c6875; font-size: .75rem; font-weight: 700; text-transform: uppercase; }
.training-facts dd, .training-metric dd { margin: .2rem 0 0; overflow-wrap: anywhere; }
.training-metric dd span { display: block; color: #5c6875; font-size: .78rem; }
.training-dataset + .training-dataset { margin-top: 1rem; border-top: 1px solid #d7dee5; }
.training-empty, .training-metric-note { color: #5c6875; }
@media (prefers-color-scheme: dark) {
  .training-table th, .training-run__header, .training-facts div, .training-metric { background: #202833; }
  .training-chart svg { background: #1a1f26; border-color: #2e3c4a; }
  .training-chart__grid { stroke: #364554; } .training-chart__axis { stroke: #9ba8b4; }
  .training-chart__label, .training-chart__tick { fill: #c8d0d8; }
}
@media print { .training-run > details { display: block; } .training-panel { display: block; } }
</style>
"""


def build_training() -> int:
    training_jsons = training_json_paths(DOCS)
    TRAINING_INDEX.parent.mkdir(parents=True, exist_ok=True)
    if not training_jsons:
        TRAINING_INDEX.write_text(
            "---\ntitle: Training\n---\n\n# Training\n\nBisher keine Training-Läufe vorhanden.\n",
            encoding="utf-8",
        )
        print("build_training: no training.json files found, wrote empty index")
        return 0

    rows = _build_rows(training_jsons)
    reports = "".join(_render_run_report(row) for row in rows if row.get("contract"))
    page = f"""---
title: Training
---

<link rel="stylesheet" href="{{{{ '/assets/catalogue.css' | relative_url }}}}">
<link rel="stylesheet" href="{{{{ '/assets/output.css' | relative_url }}}}">
<script src="{{{{ '/assets/quality-explain.js' | relative_url }}}}" defer></script>

# Training

Training runs produced by [serving-atr-inference](https://github.com/thodel/serving-atr-inference).

## Zusammenfassung

{_render_summary(rows)}

## Training runs

{_render_table(rows)}

## Laufberichte

{reports}
{_STYLES}"""
    TRAINING_INDEX.write_text(page, encoding="utf-8")
    print(f"build_training: wrote {len(rows)} training run(s) to {TRAINING_INDEX}")
    return len(rows)


if __name__ == "__main__":
    build_training()
