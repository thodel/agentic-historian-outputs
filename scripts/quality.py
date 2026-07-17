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

    The button targets an id of form ``quality-expl-{key}-{suffix}``.
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
        f'aria-expanded="false" aria-controls="quality-expl-{key}-{uniq}">'
        f'<span aria-hidden="true">ⓘ</span> {short_label}'
        f"</button>"
    )


def explanation_block(key: str, suffix: str = "") -> str:
    """Return a hidden ``<div>`` with the explanation text, plus a visible toggle.

    The div id is of form ``quality-expl-{key}-{suffix}`` to ensure uniqueness
    when the same explanation key appears multiple times on a page.
    """
    if key not in EXPLANATIONS:
        return ""
    short_label, body = EXPLANATIONS[key]
    _expl_counter[0] += 1
    uniq = suffix or str(_expl_counter[0])
    return (
        f'<div class="quality-explanation" id="quality-expl-{key}-{uniq}" '
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
