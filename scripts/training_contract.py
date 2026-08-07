#!/usr/bin/env python3
"""Validation for docs/<id>/training.json — the training run artifact.

This module is the canonical validator for the training artifact contract.
It is imported by build_training.py and by the test suite; no quality
semantics live here — only schema and referential integrity.

Schema summary (fully defined in docs/training/TRAINING_SCHEMA.md):
- doc_id:          stable document id this training run was for
- run_id:          unique training run identifier
- model_id:        registry id of the produced model
- engine:          "kraken" | "trocr" | "vlm" (engine family)
- status:          "completed" | "failed" | "cancelled"
- created_at:      ISO-8601 datetime when the job was submitted
- finished_at:     ISO-8601 datetime when the job reached a terminal state
- epochs:          requested epochs (int)
- epochs_trained:  actual epochs completed (int, 0 if never started)
- params:          hyperparameter snapshot (dict)
- metrics:         final evaluation metrics (cer/wer) or null
- curves:          per-epoch loss/accuracy data for SVG rendering (list)
- base_model:      registry id or DOI fine-tuned from, or null
- dataset:         dataset description (dict)
- log:             relative path to the stage log directory
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

# ── schema constants ─────────────────────────────────────────────────────────

VALID_ENGINES = frozenset({"kraken", "trocr", "vlm", "party"})
VALID_STATUSES = frozenset({"completed", "failed", "cancelled"})
SLUG_RE = re.compile(r"^[A-Za-z0-9]([A-Za-z0-9._-]*[A-Za-z0-9])?$", re.IGNORECASE)
MODEL_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
# tr-<model_id>-YYYYMMDD-HHMMSS
RUN_ID_RE = re.compile(r"^tr-[a-z0-9][a-z0-9._-]*-[0-9]{8}-[0-9]{6}$", re.IGNORECASE)


class ContractError(ValueError):
    """A training.json violates the contract."""


# ── curve epoch ──────────────────────────────────────────────────────────────

class CurveEpoch:
    """One training epoch's scalar values."""

    __slots__ = ("epoch", "train_loss", "val_loss", "val_accuracy", "lr")

    def __init__(
        self,
        epoch: int,
        train_loss: float | None = None,
        val_loss: float | None = None,
        val_accuracy: float | None = None,
        lr: float | None = None,
    ):
        if epoch < 0:
            raise ContractError(f"epoch must be >= 0, got {epoch}")
        for name, val in [
            ("train_loss", train_loss),
            ("val_loss", val_loss),
            ("val_accuracy", val_accuracy),
            ("lr", lr),
        ]:
            if val is not None and not isinstance(val, (int, float)):
                raise ContractError(f"{name} must be numeric, got {val!r}")
        self.epoch = epoch
        self.train_loss = float(train_loss) if train_loss is not None else None
        self.val_loss = float(val_loss) if val_loss is not None else None
        self.val_accuracy = float(val_accuracy) if val_accuracy is not None else None
        self.lr = float(lr) if lr is not None else None


# ── training.json root ───────────────────────────────────────────────────────

class TrainingContract:
    """Validated training artifact for one document."""

    __slots__ = (
        "doc_id", "run_id", "model_id", "engine", "status",
        "created_at", "finished_at",
        "epochs", "epochs_trained",
        "params", "metrics",
        "curves",
        "base_model", "dataset", "log",
        "_raw",
    )

    def __init__(self, data: dict, source_path: Path | None = None):
        self._raw = data
        self._validate(data, source_path)

        self.doc_id = data["doc_id"]
        self.run_id = data["run_id"]
        self.model_id = data["model_id"]
        self.engine = data["engine"]
        self.status = data["status"]
        self.created_at = _parse_dt(data["created_at"])
        self.finished_at = _parse_dt(data["finished_at"]) if data.get("finished_at") else None
        self.epochs = int(data["epochs"])
        self.epochs_trained = int(data.get("epochs_trained", 0))
        self.params = dict(data.get("params") or {})
        self.metrics = dict(data["metrics"]) if data.get("metrics") else None
        self.curves: list[CurveEpoch] = [
            CurveEpoch(**_ensure_dict(e)) for e in data.get("curves") or []
        ]
        self.base_model = data.get("base_model") or None
        self.dataset = dict(data.get("dataset") or {})
        self.log = data.get("log") or None

    def _validate(self, data: dict, source_path: Path | None) -> None:
        errors: list[str] = []
        path_hint = f" in {source_path}" if source_path else ""

        # ── required string fields ────────────────────────────────────────
        for field in ("doc_id", "run_id", "model_id", "engine", "status"):
            val = data.get(field)
            if not isinstance(val, str) or not val:
                errors.append(f"{field}: required non-empty string")

        # doc_id slug check
        doc_id = data.get("doc_id", "")
        if doc_id and not SLUG_RE.match(doc_id):
            errors.append(f"doc_id {doc_id!r} is not a valid document slug")

        # run_id pattern
        run_id = data.get("run_id", "")
        if run_id and not RUN_ID_RE.match(run_id):
            errors.append(
                f"run_id {run_id!r} must match pattern 'tr-<model>-YYYYMMDD-HHMMSS'"
            )

        # engine enum
        if data.get("engine") not in VALID_ENGINES:
            errors.append(
                f"engine must be one of {sorted(VALID_ENGINES)}, got {data.get('engine')!r}"
            )

        # status enum
        if data.get("status") not in VALID_STATUSES:
            errors.append(
                f"status must be one of {sorted(VALID_STATUSES)}, got {data.get('status')!r}"
            )

        # ── dates ─────────────────────────────────────────────────────────
        if not data.get("created_at"):
            errors.append("created_at: required ISO-8601 datetime")
        elif _parse_dt(data["created_at"]) is None:
            errors.append(f"created_at: invalid ISO-8601 value {data['created_at']!r}")

        finished = data.get("finished_at")
        if finished and _parse_dt(finished) is None:
            errors.append(f"finished_at: invalid ISO-8601 value {finished!r}")

        # ── numeric constraints ────────────────────────────────────────────
        epochs = data.get("epochs")
        if epochs is None:
            errors.append("epochs: required")
        elif not isinstance(epochs, (int, float)):
            errors.append(f"epochs: must be numeric, got {epochs!r}")
        elif int(epochs) < 1:
            errors.append("epochs: must be >= 1")

        et = data.get("epochs_trained", 0)
        if not isinstance(et, (int, float)):
            errors.append(f"epochs_trained: must be numeric, got {et!r}")
        elif data.get("status") == "completed" and int(et) < int(epochs):
            errors.append(
                f"epochs_trained ({et}) < epochs ({epochs}) on completed run — "
                "a completed run must have trained all requested epochs"
            )

        # ── metrics ────────────────────────────────────────────────────────
        metrics = data.get("metrics")
        if metrics is not None:
            if not isinstance(metrics, dict):
                errors.append("metrics: must be a dict or null")
            else:
                for key in ("cer", "wer"):
                    val = metrics.get(key)
                    if val is not None:
                        if not isinstance(val, (int, float)):
                            errors.append(f"metrics.{key}: must be numeric, got {val!r}")
                        elif val < 0 or val > 1:
                            errors.append(
                                f"metrics.{key}: must be 0-1 (error rate), got {val}"
                            )

        # ── curves ─────────────────────────────────────────────────────────
        curves = data.get("curves")
        if curves is not None:
            if not isinstance(curves, list):
                errors.append("curves: must be a list")
            else:
                seen: set[int] = set()
                for i, ep in enumerate(curves):
                    if not isinstance(ep, dict):
                        errors.append(f"curves[{i}]: epoch dict required, got {type(ep).__name__}")
                        continue
                    ep_num = ep.get("epoch")
                    if not isinstance(ep_num, int):
                        errors.append(f"curves[{i}].epoch: required int, got {ep_num!r}")
                    elif ep_num in seen:
                        errors.append(f"curves[{i}].epoch: duplicate {ep_num}")
                    elif ep_num != i:
                        errors.append(
                            f"curves[{i}].epoch: expected {i}, got {ep_num} — "
                            "curves must be sorted by epoch starting at 0"
                        )
                    seen.add(ep_num)

        if errors:
            raise ContractError(
                f"training.json{path_hint} contract violations:\n  - "
                + "\n  - ".join(errors)
            )

    def to_dict(self) -> dict:
        """Return the validated data as a plain dict."""
        out = dict(self._raw)
        out["curves"] = [
            {k: getattr(c, k) for k in CurveEpoch.__slots__ if getattr(c, k) is not None}
            for c in self.curves
        ]
        return out


# ── standalone validator ─────────────────────────────────────────────────────

def validate_training_json(path: Path) -> tuple[bool, str]:
    """Validate one docs/<id>/training.json.

    Returns (True, "") on success, (False, error_message) on failure.
    """
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return False, f"cannot read training.json: {exc}"

    try:
        TrainingContract(data, source_path=path)
    except ContractError as exc:
        return False, str(exc)

    return True, ""


def validate_all_training_jsons(docs_root: Path) -> dict[str, str]:
    """Scan docs_root for all */training.json and validate each.

    Returns a dict of {doc_id: error_message} for failures (empty = all valid).
    """
    results: dict[str, str] = {}
    for tpath in sorted(docs_root.glob("*/training.json")):
        doc_id = tpath.parent.name
        ok, err = validate_training_json(tpath)
        if not ok:
            results[doc_id] = err
    return results


# ── helpers ──────────────────────────────────────────────────────────────────

def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    text = str(value).strip().replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def _ensure_dict(val: object) -> dict:
    if isinstance(val, dict):
        return val
    raise ContractError(f"expected dict, got {type(val).__name__}: {val!r}")
