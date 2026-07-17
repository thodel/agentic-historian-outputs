#!/usr/bin/env python3
"""Shared quality vocabulary, provenance contract, and explanation registry.

This module is the canonical source of truth for Epic 5 quality indicators.
All other modules import from here; no quality semantics are hard-coded elsewhere.

Key concepts
------------
- Confidence (engine confidence): probability-like score produced by a recognition
  engine.  Not comparable across engines.  Always label with scope (engine/model/page).
- Agreement: proportion of engines/candidates that agree on a reading.
  Does NOT imply correctness.  Always state what was agreed on and by whom.
- Evaluation (CER/WER): Character/Word Error Rate against a known reference.
  Only present when a reference exists.  Always label reference, normalisation,
  and scope (document/page/corpus).
- Degeneration: output that is mechanically degenerate (all-same-char, empty,
  excessively long beyond reasonable bounds) even if the engine reported no error.
- Failure: recognition attempt that produced no usable output due to error,
  timeout, or degeneration.

Cardinality rules
----------------
- Engine confidence: per-candidate, never aggregated across engines.
- Agreement: per-candidate-set, never per-engine.
- Evaluation: per-output or per-page when a reference exists; absent otherwise.
- Degeneration: per-candidate flag, with human-readable explanation.
- Failure: per-candidate state, distinct from a zero-confidence success.

Provenance fields exported per candidate
----------------------------------------
- metric_type: "engine_confidence" | "agreement" | "reference_evaluation" | "degenerate" | "failed"
- metric_value: float or None
- metric_unit: str (e.g. "ratio", "CER", "WER", "probability")
- metric_scope: str (e.g. "engine/model/page", "document", "page")
- metric_provenance: dict with keys: reference, normalisation, version, dataset
- explanation_key: str used to look up the reusable explanation
- is_comparable: bool (only True when cross-engine comparison is valid)
"""

from __future__ import annotations

import html
import re
from dataclasses import dataclass, field
from typing import Literal

# ---------------------------------------------------------------------------
# Metric type vocabulary
# ---------------------------------------------------------------------------

EngineConfidenceScope = Literal["engine", "engine/model", "engine/model/page"]
MetricType = Literal[
    "engine_confidence",
    "agreement",
    "reference_evaluation",
    "degenerate",
    "failed",
    "missing",
    "legacy_qa",
]
MetricUnit = Literal["ratio", "probability", "CER", "WER", "percentage", "count", "n/a"]


# ---------------------------------------------------------------------------
# Explanation registry
# ---------------------------------------------------------------------------

# Each entry is a (short_label, body_html) tuple.
# Keys are used as explanation_key values throughout the codebase.
EXPLANATIONS: dict[str, tuple[str, str]] = {
    "engine_confidence": (
        "Engine-Konfidenz",
        "Die Engine-Konfidenz ist ein von der Erkennungs-Engine produzierter "
        "Wahrscheinlichkeitswert.  Er gilt nur für die jeweilige Engine und ist "
        "nicht mit Konfidenzwerten anderer Engines vergleichbar.  Hohe Werte bedeuten "
        "nicht notwendigerweise, dass die Transkription korrekt ist.",
    ),
    "agreement": (
        "Engine-Übereinstimmung",
        "Die Übereinstimmung zeigt, wie viele Engines dieselbe Lesart erzeugt haben.  "
        "Übereinstimmung bedeutet nicht, dass die Lesart korrekt ist — alle Engines "
        "können gemeinsam fehlgehen.  Übereinstimmungswerte sind nicht dasselbe wie "
        "Genauigkeitswerte.",
    ),
    "reference_evaluation": (
        "Referenzbasierte Auswertung (CER/WER)",
        "CER (Character Error Rate) und WER (Word Error Rate) werden gegen eine "
        "bekannte Referenztranskription berechnet.  Niedrigere Werte bedeuten weniger "
        "Fehler.  Die Metrik gilt nur für die angegebene Referenz und Normalisierung; "
        "ein anderes Referenzkorpus kann zu anderen Werten führen.",
    ),
    "degenerate": (
        "Degenerierte Ausgabe",
        "Die Erkennung hat eine degenerierte Ausgabe erzeugt (z. B. sich wiederholende "
        "Zeichen oder unerwartet lange Zeichenketten), obwohl kein technischer Fehler "
        "gemeldet wurde.  Solche Ausgaben sind mit Vorsicht zu verwenden.",
    ),
    "failed": (
        "Fehlgeschlagene Erkennung",
        "Die Erkennung ist fehlgeschlagen (Timeout, Dienst nicht erreichbar oder "
        "anderer Fehler).  Es liegt keine verwertbare Transkription vor.",
    ),
    "missing": (
        "Keine Metrik verfügbar",
        "Für diese Erkennung liegt keine Qualitätsmetrik vor.  Die Ausgabe wurde "
        "trotzdem verarbeitet; die Qualität kann nicht eingeschätzt werden.",
    ),
    "legacy_qa": (
        "Legacy-QA-Wert (unspezifiziert)",
        "Dieser QA-Wert stammt aus einem älteren System mit unbekannter Bedeutung.  "
        "Er kann nicht als Genauigkeitswert interpretiert werden.  Ersetzen Sie ihn "
        "durch eine der oben genannten Metriken.",
    ),
    "incomparable_confidence": (
        "Nicht vergleichbare Konfidenzwerte",
        "Konfidenzwerte verschiedener Engines stammen aus unterschiedlichen Modellen "
        "mit unterschiedlichen Skalen und Bedeutungen.  Ein höherer Wert einer Engine "
        "bedeutet nicht, dass deren Transkription genauer ist als die einer anderen Engine.",
    ),
    "verification_needed": (
        "Menschliche Überprüfung empfohlen",
        "Diese Transkription ist maschinell erzeugt.  Sie sollte anhand des "
        "Originaldokuments überprüft werden, bevor sie in einer wissenschaftlichen "
        "Arbeit zitiert wird.",
    ),
}


# ---------------------------------------------------------------------------
# Provenance record
# ---------------------------------------------------------------------------

@dataclass
class Provenance:
    """Provenance metadata for a quality metric."""
    metric_type: MetricType
    value: float | None = None
    unit: MetricUnit = "n/a"
    scope: str = "n/a"
    # Reference evaluation provenance
    reference_name: str | None = None
    reference_version: str | None = None
    normalisation: str | None = None
    dataset: str | None = None
    # Producer info
    engine: str | None = None
    model: str | None = None
    page: str | None = None
    # Computed flags
    is_comparable: bool = False
    explanation_key: str = "missing"
    # Raw values preserved for machine-readable export
    raw: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "metric_type": self.metric_type,
            "value": self.value,
            "unit": self.unit,
            "scope": self.scope,
            "reference_name": self.reference_name,
            "reference_version": self.reference_version,
            "normalisation": self.normalisation,
            "dataset": self.dataset,
            "engine": self.engine,
            "model": self.model,
            "page": self.page,
            "is_comparable": self.is_comparable,
            "explanation_key": self.explanation_key,
        }


# ---------------------------------------------------------------------------
# Degeneration detection
# ---------------------------------------------------------------------------

DEGENERATE_PATTERNS = [
    (re.compile(r"^(.)\1{19,}$"), "wiederholtes Zeichen"),       # 20+ same char
    (re.compile(r"^(.{1,5})\1{9,}$"), "wiederholte Sequenz"),    # 10+ repeats of ≤5-char seq
    (re.compile(r"^[\s\n]{50,}$"), "nur Leerzeichen"),            # 50+ whitespace only
]


def detect_degeneration(text: str, confidence: float | None = None) -> tuple[bool, str]:
    """Return (is_degenerate, reason)."""
    if not text:
        return True, "kein Text"
    if confidence is not None and confidence < 0.01:
        return True, "sehr niedrige Engine-Konfidenz"
    for pattern, label in DEGENERATE_PATTERNS:
        if pattern.match(text):
            return True, f"degenerierte Ausgabe ({label})"
    if len(text) > 1_000_000:
        return True, "unrealistisch lange Ausgabe"
    return False, ""


# ---------------------------------------------------------------------------
# Typed quality label helpers
# ---------------------------------------------------------------------------

def format_confidence(value: float | None) -> str:
    """Format confidence as a human-readable percentage."""
    if value is None:
        return "Nicht angegeben"
    return f"{max(0.0, min(1.0, float(value))):.0%}"


def format_ratio(value: float | None, invert: bool = False) -> str:
    """Format a ratio value as percentage; invert=True for CER/WER (lower = better)."""
    if value is None:
        return "Nicht angegeben"
    pct = max(0.0, min(1.0, float(value))) * 100
    if invert:
        return f"{pct:.1f} % (niedrig = besser)"
    return f"{pct:.1f} %"


def legacy_qa_score(value: object) -> tuple[bool, str]:
    """Interpret legacy qa_score field.

    Returns (is_legacy_qa, human_readable_label).
    Legacy qa_score was a raw float stored in a_meta.qa_score without
    unit, scope, or provenance context.
    """
    if value is None:
        return False, ""
    try:
        float_val = float(value)
    except (TypeError, ValueError):
        return False, ""
    if not (0.0 <= float_val <= 1.0):
        return False, ""
    return True, f"Legacy-QA {float_val:.0%}"


def quality_badge(kind: MetricType, value: float | None, unit: MetricUnit,
                  scope: str, is_legacy: bool = False) -> str:
    """Return a typed quality badge HTML string."""
    if is_legacy:
        ek = "legacy_qa"
        label = f"Legacy-QA {value:.0%}" if value is not None else "Legacy-QA"
    elif kind == "engine_confidence":
        ek = "engine_confidence"
        label = f"Konfidenz {format_confidence(value)}"
    elif kind == "agreement":
        ek = "agreement"
        label = f"Übereinstimmung {format_ratio(value)}"
    elif kind == "reference_evaluation":
        ek = "reference_evaluation"
        unit_label = "CER" if unit == "CER" else "WER"
        label = f"{unit_label} {format_ratio(value, invert=True)}"
    elif kind == "degenerate":
        ek = "degenerate"
        label = "Degenerierte Ausgabe"
    elif kind == "failed":
        ek = "failed"
        label = "Fehlgeschlagen"
    else:
        ek = "missing"
        label = "Keine Qualitätsmetrik"
    return (
        f'<span class="quality-badge quality-badge--{kind}" '
        f'title="{EXPLANATIONS.get(ek, ("", ""))[1]}">{label}</span>'
    )


# ---------------------------------------------------------------------------
# Accessible explanation disclosure
# ---------------------------------------------------------------------------

_expl_counter = [0]

def explanation_button(key: str, suffix: str = "") -> str:
    """Return an accessible ``<button>`` that toggles an inline explanation.

    The button targets an id of form ``quality-explanation-{key}-{suffix}``.
    When suffix is empty, a global counter increments to ensure uniqueness.
    CSS shows/hides the linked element.  Keyboard, touch, and screen-reader
    accessible by default (native <button> + aria-expanded + aria-controls).
    """
    if key not in EXPLANATIONS:
        return ""
    short_label, _ = EXPLANATIONS[key]
    _expl_counter[0] += 1
    uniq = suffix or str(_expl_counter[0])
    return (
        f'<button class="quality-explain-btn" type="button" '
        f'aria-expanded="false" aria-controls="quality-explanation-{key}-{uniq}">'
        f'<span aria-hidden="true">ⓘ</span> {short_label}'
        f"</button>"
    )


def explanation_block(key: str, suffix: str = "") -> str:
    """Return a hidden ``<div>`` with the explanation text, plus a visible toggle.

    The div id is of form ``quality-explanation-{key}-{suffix}`` to ensure
    uniqueness when the same explanation key appears multiple times.
    """
    if key not in EXPLANATIONS:
        return ""
    short_label, body = EXPLANATIONS[key]
    _expl_counter[0] += 1
    uniq = suffix or str(_expl_counter[0])
    return (
        f'<div class="quality-explanation" id="quality-explanation-{key}-{uniq}" '
        f'role="region" aria-label="{html.escape(short_label)}" hidden>'
        f"<p><strong>{short_label}:</strong> {body}</p>"
        f"</div>"
    )


# ---------------------------------------------------------------------------
# Confidence scope labelling
# ---------------------------------------------------------------------------

def confidence_scope_label(engine: str, model: str | None, page: str | None) -> str:
    """Human-readable scope label for an engine confidence value."""
    if page:
        return f"{engine}/{model or '?'}/Seite {page}" if model else f"{engine}/Seite {page}"
    if model:
        return f"{engine}/{model}"
    return engine


# ---------------------------------------------------------------------------
# Reference evaluation display helpers
# ---------------------------------------------------------------------------

def evaluation_scope_label(scope: str) -> str:
    """Return a human-readable German label for an evaluation scope."""
    _labels: dict[str, str] = {
        "candidate": "Einzelkandidat",
        "page": "Seite",
        "document": "Dokument",
        "corpus": "Korpus",
        "run": "Durchlauf",
        "n/a": "k. A.",
    }
    return _labels.get(scope, scope)


def is_evaluation_available(candidate: dict) -> bool:
    """Return True only when *candidate* contains a usable reference evaluation.

    A reference evaluation is usable when it has a ``reference_name`` — without
    a named reference, the metric cannot be traced to its provenance.
    """
    if not isinstance(candidate, dict):
        return False
    # Preferred location: embedded reference_eval sub-dict
    ref_eval = candidate.get("reference_eval")
    if isinstance(ref_eval, dict) and ref_eval.get("reference_name"):
        return True
    # Fall back: top-level metric_type field
    if (
        candidate.get("metric_type") == "reference_evaluation"
        and candidate.get("reference_name")
    ):
        return True
    return False


def render_evaluation_unavailable(suffix: str = "") -> str:
    """Return accessible HTML notice for absent or missing reference evaluation."""
    _expl_counter[0] += 1
    return (
        '<p class="quality-eval-unavailable" '
        'aria-label="Keine Referenzauswertung verfügbar">'
        '<span class="quality-badge quality-badge--missing" aria-hidden="true">⊘</span>'
        " Keine Referenzauswertung verfügbar\u2009—\u2009"
        "kein Referenzdatensatz für diesen Kandidaten."
        "</p>"
    )


def render_reference_evaluation(
    prov: "Provenance",
    suffix: str = "",
    doc_id: str = "",
) -> str:
    """Return fully provenance-annotated HTML for a reference evaluation metric.

    Shows CER/WER with reference name, normalization, scope, dataset, and version.
    Includes:
    - A typed quality badge with the metric value
    - An accessible explanation button/block
    - A provenance table (reference, scope, version, normalization, dataset)
    - A ``data-provenance`` attribute with the machine-readable Provenance dict
    - A ``<details>`` element with a stable JSON export for download/tracing
    - A corpus-scope warning when scope is "corpus"

    Falls back to :func:`render_evaluation_unavailable` when *prov* is not a
    ``reference_evaluation`` Provenance.
    """
    import json as _json

    if prov is None or prov.metric_type != "reference_evaluation":
        return render_evaluation_unavailable(suffix)

    _expl_counter[0] += 1
    uniq = suffix or str(_expl_counter[0])

    # Format the metric value
    if prov.value is not None:
        pct = prov.value * 100
        value_str = f"{pct:.1f}\u202f%"
        aria_value = f"{prov.unit}\u00a0{value_str} (niedrig\u00a0=\u00a0besser)"
    else:
        value_str = "nicht angegeben"
        aria_value = f"{prov.unit}: Wert nicht angegeben"

    scope_label = evaluation_scope_label(prov.scope)
    ref_display = html.escape(prov.reference_name or "Unbekannte Referenz")

    # Provenance table rows
    rows: list[str] = [
        f"<tr><th scope=\"row\">Referenz</th><td>{ref_display}</td></tr>",
        (
            f"<tr><th scope=\"row\">Auswertungsebene</th>"
            f"<td>{html.escape(scope_label)}</td></tr>"
        ),
    ]
    if prov.reference_version:
        rows.append(
            f"<tr><th scope=\"row\">Referenzversion</th>"
            f"<td>{html.escape(prov.reference_version)}</td></tr>"
        )
    if prov.normalisation:
        rows.append(
            f"<tr><th scope=\"row\">Normalisierung</th>"
            f"<td>{html.escape(prov.normalisation)}</td></tr>"
        )
    if prov.dataset:
        rows.append(
            f"<tr><th scope=\"row\">Datensatz</th>"
            f"<td>{html.escape(prov.dataset)}</td></tr>"
        )

    # Corpus-scope warning: must not be read as document-level accuracy
    corpus_warning = ""
    if prov.scope == "corpus":
        corpus_warning = (
            '<p class="quality-corpus-warning" role="note">'
            "<strong>Hinweis:</strong> Dieser Wert gilt für das gesamte Korpus "
            "und darf nicht als Dokumentgenauigkeit interpretiert werden."
            "</p>"
        )

    # Machine-readable data attribute (compact)
    machine_data = html.escape(_json.dumps(prov.to_dict(), ensure_ascii=False))

    # Full JSON export shown in <details>
    export_payload = {
        "schema": "agentic-historian/reference-evaluation/v1",
        "doc_id": doc_id,
        "metric_type": prov.metric_type,
        "unit": prov.unit,
        "value": prov.value,
        "scope": prov.scope,
        "reference_name": prov.reference_name,
        "reference_version": prov.reference_version,
        "normalisation": prov.normalisation,
        "dataset": prov.dataset,
        "engine": prov.engine,
        "model": prov.model,
        "page": prov.page,
        "is_comparable": prov.is_comparable,
        "explanation_key": prov.explanation_key,
    }
    export_json_str = html.escape(
        _json.dumps(export_payload, ensure_ascii=False, indent=2)
    )

    expl_btn = explanation_button("reference_evaluation", uniq)
    expl_blk = explanation_block("reference_evaluation", uniq)
    rows_html = "\n".join(rows)

    return (
        f'<div class="quality-reference-eval" '
        f'data-provenance="{machine_data}" '
        f'aria-label="Referenzbasierte Auswertung: {html.escape(aria_value)}">'
        f'<p class="quality-eval-summary">'
        f'<span class="quality-badge quality-badge--eval">'
        f"{html.escape(prov.unit)}\u00a0{value_str}"
        f"</span>"
        f" {expl_btn}"
        f"</p>"
        f"{corpus_warning}"
        f'<table class="quality-provenance-table" '
        f'aria-label="Auswertungsherkunft">'
        f"<tbody>{rows_html}</tbody>"
        f"</table>"
        f"{expl_blk}"
        f'<details class="quality-machine-export">'
        f"<summary>Maschinenlesbare Herkunftsdaten</summary>"
        f'<pre><code class="language-json">{export_json_str}</code></pre>'
        f"</details>"
        f"</div>"
    )


# ---------------------------------------------------------------------------
# Machine-readable quality export
# ---------------------------------------------------------------------------

def quality_summary_json(record: Provenance | None) -> str:
    """Return a compact JSON string for machine-readable quality data."""
    import json
    if record is None:
        return "{}"
    return json.dumps(record.to_dict(), ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# CSS class constants (used by other modules)
# ---------------------------------------------------------------------------

BADGE_CLASS_MAP: dict[MetricType, str] = {
    "engine_confidence": "quality-badge--confidence",
    "agreement": "quality-badge--agreement",
    "reference_evaluation": "quality-badge--eval",
    "degenerate": "quality-badge--degenerate",
    "failed": "quality-badge--failed",
    "missing": "quality-badge--missing",
    "legacy_qa": "quality-badge--legacy",
}


# ---------------------------------------------------------------------------
# Comparability rules (machine-readable contract)
# ---------------------------------------------------------------------------

# Which metric kinds may be compared across candidates from *different producers*?
# A metric is only cross-comparable when the values are on the same absolute scale
# with the same meaning regardless of who produced them.
#
# engine_confidence   — NOT cross-comparable.  Scale and calibration differ per
#                       engine/model.  Only ordinal within a single engine series.
# agreement           — NOT cross-comparable across independent candidate-sets.
# reference_evaluation — comparable only within the same (reference, normalisation,
#                        scope) triple.  Different references yield different values.
# degenerate/failed   — boolean states; comparison is not meaningful.
# missing/legacy_qa   — value is unknown or undefined; comparison is invalid.

COMPARABILITY_RULES: dict[str, bool] = {
    "engine_confidence": False,
    "agreement": False,
    "reference_evaluation": False,   # see note above – caller must verify same context
    "degenerate": False,
    "failed": False,
    "missing": False,
    "legacy_qa": False,
}

# Comparability within the same (metric_type, engine, model, reference_name,
# reference_version, normalisation, scope) tuple:
SAME_CONTEXT_COMPARABLE: dict[str, bool] = {
    "engine_confidence": True,
    "agreement": True,
    "reference_evaluation": True,
    "degenerate": False,
    "failed": False,
    "missing": False,
    "legacy_qa": False,
}


# ---------------------------------------------------------------------------
# Metric-level scopes
# ---------------------------------------------------------------------------

# Allowed scope strings and what they mean:
#
# "candidate"   — attached to a single recognition candidate (one engine/model/page)
# "page"        — aggregated over all candidates on a single page
# "document"    — aggregated over all pages in one document
# "corpus"      — aggregated over multiple documents; must NOT be displayed as
#                 document-level accuracy.
# "run"         — a single pipeline execution (may span multiple pages)
# "n/a"         — scope is not applicable (e.g. boolean failure flags)

VALID_SCOPES = frozenset(
    {"candidate", "page", "document", "corpus", "run", "n/a"}
)

# Scopes that are allowed per metric type:
SCOPE_CONSTRAINTS: dict[str, frozenset] = {
    "engine_confidence": frozenset({"candidate", "page"}),
    "agreement": frozenset({"candidate", "page", "document"}),
    "reference_evaluation": frozenset({"candidate", "page", "document", "corpus"}),
    "degenerate": frozenset({"candidate", "n/a"}),
    "failed": frozenset({"candidate", "n/a"}),
    "missing": frozenset({"n/a"}),
    "legacy_qa": frozenset({"candidate", "page", "document", "n/a"}),
}


# ---------------------------------------------------------------------------
# Canonical normalization: raw pipeline payloads → Provenance
# ---------------------------------------------------------------------------
#
# Input payloads come from three sources:
#   1. Current pipeline JSON (recognitions[] entries with typed fields)
#   2. Legacy a_meta with qa_score / confidence / fusion fields
#   3. Partially-filled or unknown payloads (result: Provenance("missing"))
#
# Rules enforced:
#   - Percentages are only emitted when a range/unit is known.
#   - engine_confidence must carry an engine; without one it degrades to missing.
#   - reference_evaluation must carry reference_name; without one it degrades to missing.
#   - Corpus-level results must have scope="corpus" and are never silently document-level.

class NormalizationError(ValueError):
    """Raised when a payload violates a hard contract rule."""


def _coerce_float(value: object) -> float | None:
    """Coerce value to float in [0, 1], or None if not possible."""
    if value is None:
        return None
    try:
        f = float(value)
    except (TypeError, ValueError):
        return None
    return max(0.0, min(1.0, f))


def _coerce_ratio_or_cer(value: object) -> float | None:
    """Coerce a CER/WER value: accept [0,1] floats; reject values >1 (percentages
    stored without dividing by 100 are ambiguous and must not be silently accepted)."""
    if value is None:
        return None
    try:
        f = float(value)
    except (TypeError, ValueError):
        return None
    if f < 0:
        return None
    if f > 1.0:
        # Values > 1 are almost certainly raw percentages stored incorrectly.
        # Emit None rather than silently dividing by 100 and emitting a wrong value.
        return None
    return f


def normalize_metric(payload: dict) -> "Provenance":
    """Normalize a raw pipeline or legacy metric payload to a Provenance record.

    This is the canonical entry point for all incoming metric data.  It:
    - Detects and normalises legacy qa_score / confidence / fusion payloads.
    - Validates required fields for each metric type.
    - Enforces scope constraints and comparability rules.
    - Returns Provenance(metric_type="missing") for anything that cannot be
      resolved safely.

    Parameters
    ----------
    payload:
        A dict with any combination of the following keys:
        - ``metric_type``: one of the MetricType literals (current format)
        - ``qa_score``: legacy float in [0, 1]
        - ``confidence``: per-candidate engine confidence float
        - ``engine``, ``model``, ``page``: producer identification
        - ``cer``, ``wer``: reference evaluation values in [0, 1]
        - ``reference_name``, ``reference_version``, ``normalisation``, ``dataset``: reference evaluation context
        - ``scope``: metric level (candidate/page/document/corpus/run/n/a)
        - ``agreement``: ensemble agreement float
        - ``failed``: bool or truthy value
        - ``degenerate``: bool or truthy value

    Returns
    -------
    Provenance
    """
    if not isinstance(payload, dict):
        return Provenance(metric_type="missing", explanation_key="missing")

    raw = dict(payload)  # keep a copy for .raw

    # -----------------------------------------------------------------
    # 1. Explicit failure / degeneration states take priority
    # -----------------------------------------------------------------
    if payload.get("failed") or payload.get("error"):
        return Provenance(
            metric_type="failed",
            scope="n/a",
            explanation_key="failed",
            is_comparable=False,
            raw=raw,
        )

    if payload.get("degenerate"):
        return Provenance(
            metric_type="degenerate",
            scope="n/a",
            explanation_key="degenerate",
            is_comparable=False,
            raw=raw,
        )

    # -----------------------------------------------------------------
    # 2. Explicit metric_type field (current pipeline format)
    # -----------------------------------------------------------------
    explicit_type = payload.get("metric_type")

    if explicit_type == "engine_confidence":
        engine = payload.get("engine") or ""
        if not engine:
            # engine_confidence without an engine is unsafe to display
            return Provenance(metric_type="missing", explanation_key="missing", raw=raw)
        value = _coerce_float(payload.get("value"))
        scope = payload.get("scope", "candidate")
        if scope not in SCOPE_CONSTRAINTS["engine_confidence"]:
            scope = "candidate"
        return Provenance(
            metric_type="engine_confidence",
            value=value,
            unit="probability",
            scope=scope,
            engine=engine,
            model=payload.get("model") or None,
            page=payload.get("page") or None,
            is_comparable=False,
            explanation_key="engine_confidence",
            raw=raw,
        )

    if explicit_type == "agreement":
        value = _coerce_float(payload.get("value"))
        scope = payload.get("scope", "candidate")
        if scope not in SCOPE_CONSTRAINTS["agreement"]:
            scope = "candidate"
        return Provenance(
            metric_type="agreement",
            value=value,
            unit="ratio",
            scope=scope,
            is_comparable=False,
            explanation_key="agreement",
            raw=raw,
        )

    if explicit_type == "reference_evaluation":
        ref_name = payload.get("reference_name") or ""
        if not ref_name:
            # reference_evaluation without a reference is unsafe to display
            return Provenance(metric_type="missing", explanation_key="missing", raw=raw)
        # Prefer CER; fall back to WER; reject values outside [0,1]
        cer_val = _coerce_ratio_or_cer(payload.get("cer"))
        wer_val = _coerce_ratio_or_cer(payload.get("wer"))
        value = cer_val if cer_val is not None else wer_val
        unit: MetricUnit = "CER" if cer_val is not None else ("WER" if wer_val is not None else "n/a")
        scope = payload.get("scope", "document")
        if scope not in SCOPE_CONSTRAINTS["reference_evaluation"]:
            scope = "document"
        return Provenance(
            metric_type="reference_evaluation",
            value=value,
            unit=unit,
            scope=scope,
            reference_name=ref_name,
            reference_version=payload.get("reference_version") or None,
            normalisation=payload.get("normalisation") or None,
            dataset=payload.get("dataset") or None,
            is_comparable=False,
            explanation_key="reference_evaluation",
            raw=raw,
        )

    # -----------------------------------------------------------------
    # 3. Legacy payload detection (qa_score, confidence, fusion)
    # -----------------------------------------------------------------

    # Legacy: inline confidence field + engine field (pre-contract candidates)
    if "confidence" in payload and payload.get("engine"):
        value = _coerce_float(payload.get("confidence"))
        engine = str(payload["engine"])
        scope = payload.get("scope", "candidate")
        if scope not in SCOPE_CONSTRAINTS["engine_confidence"]:
            scope = "candidate"
        return Provenance(
            metric_type="engine_confidence",
            value=value,
            unit="probability",
            scope=scope,
            engine=engine,
            model=payload.get("model_id") or payload.get("model") or None,
            page=payload.get("page") or None,
            is_comparable=False,
            explanation_key="engine_confidence",
            raw=raw,
        )

    # Legacy: qa_score — stored as an unlabelled float in a_meta
    if "qa_score" in payload and payload["qa_score"] is not None:
        value = _coerce_float(payload["qa_score"])
        if value is not None:
            return Provenance(
                metric_type="legacy_qa",
                value=value,
                unit="n/a",
                scope="n/a",
                is_comparable=False,
                explanation_key="legacy_qa",
                raw=raw,
            )

    # Legacy: agreement field only (no engine context)
    if "agreement" in payload and payload["agreement"] is not None:
        value = _coerce_float(payload["agreement"])
        return Provenance(
            metric_type="agreement",
            value=value,
            unit="ratio",
            scope=payload.get("scope", "candidate"),
            is_comparable=False,
            explanation_key="agreement",
            raw=raw,
        )

    # -----------------------------------------------------------------
    # 4. Fallback: missing / not applicable
    # -----------------------------------------------------------------
    return Provenance(metric_type="missing", explanation_key="missing", raw=raw)


def normalize_candidate_metrics(candidate: dict) -> "Provenance":
    """Derive a single best-effort Provenance for a recognition candidate dict.

    Priority: failed/degenerate > reference_evaluation > engine_confidence
    > agreement > legacy_qa > missing.
    """
    if not isinstance(candidate, dict):
        return Provenance(metric_type="missing", explanation_key="missing")

    # Failure/degeneration states
    if candidate.get("error") or candidate.get("failed"):
        return normalize_metric({"failed": True, "error": candidate.get("error"), **candidate})
    if candidate.get("degenerate"):
        return normalize_metric({"degenerate": True, **candidate})

    # Reference evaluation embedded in candidate
    ref_eval = candidate.get("reference_eval")
    if isinstance(ref_eval, dict) and ref_eval.get("reference_name"):
        return normalize_metric({"metric_type": "reference_evaluation", **ref_eval})

    # Engine confidence
    if candidate.get("confidence") is not None and candidate.get("engine"):
        return normalize_metric(
            {
                "metric_type": "engine_confidence",
                "value": candidate["confidence"],
                "engine": candidate["engine"],
                "model": candidate.get("model_id") or candidate.get("model"),
                "page": candidate.get("page"),
                "scope": "candidate",
            }
        )

    # Agreement
    if candidate.get("agreement") is not None:
        return normalize_metric({"metric_type": "agreement", "value": candidate["agreement"], "scope": "candidate"})

    # Legacy qa_score
    if candidate.get("qa_score") is not None:
        return normalize_metric({"qa_score": candidate["qa_score"]})

    return Provenance(metric_type="missing", explanation_key="missing")

