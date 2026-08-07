#!/usr/bin/env python3
"""Validation for docs/training/<run_id>/training.json — the training artifact.

This module is the canonical validator for the training artifact contract.
It is imported by build_training.py and by the test suite; no quality
semantics live here — only schema and referential integrity.

A training run is about **datasets, not documents**. It consumes one or more
HuggingFace datasets and produces a model; it is not made "for" any single
catalogue document, and a run over 18,000 pages from eight projects has no
document to be filed under. Runs therefore live at
``docs/training/<run_id>/training.json`` and are keyed by ``run_id``.

Schema summary (fully defined in docs/training/TRAINING_SCHEMA.md):
- schema_version:  contract version (int), so older runs keep rendering
- run_id:          unique training run identifier; also its directory name
- model_id:        registry id of the produced model
- engine:          "kraken" | "vllm" | "trocr" (engine family)
- status:          "completed" | "failed" | "cancelled"
- created_at:      ISO-8601 datetime when the job was submitted
- finished_at:     ISO-8601 datetime when the job reached a terminal state
- epochs:          requested epochs (int)
- epochs_trained:  actual epochs completed (int, 0 if never started)
- params:          hyperparameter snapshot (dict)
- metrics:         final evaluation metrics (cer/wer) or null
- curves:          per-epoch loss/accuracy data for SVG rendering (list)
- base_model:      registry id or DOI fine-tuned from, or null
- datasets:        1..n HuggingFace datasets the run consumed (list of dicts)
- log:             relative path to the stage log directory
"""

from __future__ import annotations

import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path

# ── schema constants ─────────────────────────────────────────────────────────

# party is deliberately absent: it is a served engine, not a trainable one.
VALID_ENGINES = frozenset({"kraken", "vllm", "trocr"})
CURRENT_SCHEMA_VERSION = 1
VALID_STATUSES = frozenset({"completed", "failed", "cancelled"})
SLUG_RE = re.compile(r"^[A-Za-z0-9]([A-Za-z0-9._-]*[A-Za-z0-9])?$", re.IGNORECASE)
MODEL_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
# A run id becomes a directory name, so it must be a safe slug — but the FORMAT
# is the producer's business, not ours. serving-atr-inference emits
# "20260807T161137Z-kraken-medieval-scripts-v1"; pinning a "tr-<model>-<date>"
# pattern here would reject every real run for no benefit to a reader.
RUN_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{2,127}$")
# owner/name, as on the hub
HF_REPO_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*/[A-Za-z0-9][A-Za-z0-9._-]*$")
REVISION_RE = re.compile(r"^[A-Za-z0-9._-]{7,128}$")


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
            if val is not None and (
                not isinstance(val, (int, float))
                or isinstance(val, bool)
                or not math.isfinite(float(val))
            ):
                raise ContractError(f"{name} must be a finite number, got {val!r}")
        self.epoch = epoch
        self.train_loss = float(train_loss) if train_loss is not None else None
        self.val_loss = float(val_loss) if val_loss is not None else None
        self.val_accuracy = float(val_accuracy) if val_accuracy is not None else None
        self.lr = float(lr) if lr is not None else None


# ── training.json root ───────────────────────────────────────────────────────

class TrainingContract:
    """Validated training artifact for one training run."""

    __slots__ = (
        "schema_version", "run_id", "model_id", "engine", "status",
        "created_at", "finished_at",
        "epochs", "epochs_trained",
        "params", "metrics",
        "curves",
        "base_model", "datasets", "log",
        "_raw",
    )

    def __init__(self, data: dict, source_path: Path | None = None):
        self._raw = data
        self._validate(data, source_path)

        self.schema_version = int(data.get("schema_version", CURRENT_SCHEMA_VERSION))
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
        self.datasets = [dict(d) for d in data.get("datasets") or []]
        self.log = data.get("log") or None

    def _validate(self, data: dict, source_path: Path | None) -> None:
        errors: list[str] = []
        path_hint = f" in {source_path}" if source_path else ""

        # ── required string fields ────────────────────────────────────────
        for field in ("run_id", "model_id", "engine", "status"):
            val = data.get(field)
            if not isinstance(val, str) or not val:
                errors.append(f"{field}: required non-empty string")

        # schema_version — present and known, so a future producer cannot be
        # rendered silently wrong by an older site build
        version = data.get("schema_version", CURRENT_SCHEMA_VERSION)
        if not isinstance(version, int) or version < 1:
            errors.append(f"schema_version: must be a positive int, got {version!r}")
        elif version > CURRENT_SCHEMA_VERSION:
            errors.append(
                f"schema_version {version} is newer than this site understands "
                f"({CURRENT_SCHEMA_VERSION}) — update the site before publishing it"
            )

        # run_id doubles as a directory name
        run_id = data.get("run_id", "")
        if run_id and not RUN_ID_RE.match(run_id):
            errors.append(
                f"run_id {run_id!r} is not a safe directory slug "
                f"(expected {RUN_ID_RE.pattern})"
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
        elif data.get("status") == "completed" and int(et) < 1:
            errors.append(
                "epochs_trained: a completed run must have trained at least one epoch"
            )
        elif isinstance(epochs, (int, float)) and int(et) > int(epochs):
            errors.append(
                f"epochs_trained ({et}) > epochs ({epochs}) — more epochs than requested"
            )

        params = data.get("params")
        if params is not None and not isinstance(params, dict):
            errors.append("params: must be a dict when present")

        for field in ("base_model", "log"):
            value = data.get(field)
            if value is not None and not isinstance(value, str):
                errors.append(f"{field}: must be a string or null")
        # NOTE: epochs_trained < epochs is NOT an error. `quit: early` stops when
        # the validation metric stops improving, which is the recommended setting
        # for fine-tuning; requiring the full count would reject every early-stopped
        # run as malformed.

        # ── datasets (1..n, always) ────────────────────────────────────────
        # Training always consumes datasets from the hub. One is the common case,
        # several is a first-class one: a model trained on medieval-scripts plus
        # kurrent-xix is a different model, and a report that could only name one
        # of them would misdescribe it.
        datasets = data.get("datasets")
        if not isinstance(datasets, list) or not datasets:
            errors.append("datasets: required, at least one dataset must be listed")
        else:
            for i, ds in enumerate(datasets):
                if not isinstance(ds, dict):
                    errors.append(f"datasets[{i}]: must be a dict, got {type(ds).__name__}")
                    continue
                repo = ds.get("hf_repo")
                if not isinstance(repo, str) or not HF_REPO_RE.match(repo or ""):
                    errors.append(
                        f"datasets[{i}].hf_repo: required, 'owner/name' on the hub, "
                        f"got {repo!r}"
                    )
                for key in ("train_projects", "eval_projects"):
                    val = ds.get(key)
                    if val is not None and not isinstance(val, list):
                        errors.append(f"datasets[{i}].{key}: must be a list when present")
                    elif isinstance(val, list) and any(
                        not isinstance(item, str) or not item.strip() for item in val
                    ):
                        errors.append(
                            f"datasets[{i}].{key}: entries must be non-empty strings"
                        )
                revision = ds.get("revision")
                if revision is not None and (
                    not isinstance(revision, str) or not REVISION_RE.fullmatch(revision)
                ):
                    errors.append(
                        f"datasets[{i}].revision: expected a safe revision id"
                    )
                split = ds.get("split")
                if split is not None and (not isinstance(split, str) or not split.strip()):
                    errors.append(f"datasets[{i}].split: must be a non-empty string")
                for key in ("pages", "lines", "chars", "pages_skipped"):
                    val = ds.get(key)
                    if val is not None and (not isinstance(val, int) or val < 0):
                        errors.append(
                            f"datasets[{i}].{key}: must be a non-negative int when present"
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
                for key in ("char_accuracy", "char_accuracy_ci", "word_accuracy"):
                    val = metrics.get(key)
                    if val is not None and (
                        not isinstance(val, (int, float))
                        or isinstance(val, bool)
                        or not math.isfinite(float(val))
                        or val < 0 or val > 100
                    ):
                        errors.append(f"metrics.{key}: must be a finite percentage 0-100")
                for key in ("chars", "errors"):
                    val = metrics.get(key)
                    if val is not None and (
                        not isinstance(val, int) or isinstance(val, bool) or val < 0
                    ):
                        errors.append(f"metrics.{key}: must be a non-negative int")
                if (
                    isinstance(metrics.get("chars"), int)
                    and isinstance(metrics.get("errors"), int)
                    and metrics["errors"] > metrics["chars"]
                ):
                    errors.append("metrics.errors cannot exceed metrics.chars")

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
                    for key in ("train_loss", "val_loss", "val_accuracy", "lr"):
                        val = ep.get(key)
                        if val is not None and (
                            not isinstance(val, (int, float))
                            or isinstance(val, bool)
                            or not math.isfinite(float(val))
                        ):
                            errors.append(
                                f"curves[{i}].{key}: must be a finite number"
                            )

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
    """Validate one docs/training/<run_id>/training.json.

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


def training_json_paths(docs_root: Path) -> list[Path]:
    """Every training record, in run-id order.

    Runs live under ``docs/training/<run_id>/`` — not under a document, because a
    run belongs to its datasets, not to any one catalogue entry.
    """
    return sorted(docs_root.glob("training/*/training.json"))


def validate_all_training_jsons(docs_root: Path) -> dict[str, str]:
    """Validate every training record found under docs_root.

    Returns a dict of {run_id: error_message} for failures (empty = all valid).
    """
    results: dict[str, str] = {}
    for tpath in training_json_paths(docs_root):
        run_id = tpath.parent.name
        ok, err = validate_training_json(tpath)
        if not ok:
            results[run_id] = err
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
