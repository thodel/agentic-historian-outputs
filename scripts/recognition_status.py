#!/usr/bin/env python3
"""Recognition attempt status taxonomy and sanitisation helpers.

This module provides the canonical status vocabulary for issue #49.

Status codes
------------
Each status is one of:

  success          — recognition produced usable output (text may still be
                     degenerate; see ``degenerate`` status)
  empty            — recognition produced output that is completely empty
                     (zero characters); distinct from ``degenerate`` to
                     allow different retry semantics (empty may succeed on
                     retry; true degeneration will not)
  timeout          — the recognition service did not respond within its
                     configured time limit; retrying *may* succeed
  unavailable      — the recognition service was unreachable (connection
                     refused, DNS failure, 5xx from service); retrying
                     *may* succeed
  unsupported_model — the requested model does not exist or is not available
                       on this service; retrying will not help without
                       switching engine or model
  backend_error    — the recognition service returned an error after
                       accepting the request (4xx, 5xx, or unhandled
                       exception); retrying *may* succeed
  invalid_response — the service returned a response that could not be
                       parsed or was structurally invalid; retrying *may*
                       yield a different result
  cancelled        — the recognition was explicitly cancelled before
                       completion; retrying may help if the cancellation
                       was premature
  degenerate       — recognition produced output that is mechanically
                       degenerate (repeating characters, or unreasonably
                       long) even though the engine reported no error;
                       retrying will not improve the output without a
                       different engine/model
  missing          — no recognition was attempted at all (e.g. because
                       source page has no image); no output exists and
                       retrying requires first-class source data

Every status is classified along two axes:

  retryable  — retrying with the same inputs *might* yield a better result
  complete   — the recognition attempt finished (False means it was
               interrupted/cancelled before producing any output)

Backward compatibility
----------------------
The ``normalize()`` function converts legacy field shapes:

  • plain-text ``error`` string from old pipeline runs
  • ``error_code`` field (numeric or string) if present
  • ``status`` field with any legacy label

The ``Status`` dataclass exposes three levels of detail:

  public_msg   — safe for pages, downloads, API responses
  diagnostic   — internal use; may contain safe technical detail
  raw          — original pipeline fields, unsanitised

Canonical export (``to_dict()``) includes provenance context::

  {
    "status_code": "timeout",
    "retryable": true,
    "complete": true,
    "public_msg": "Der Erkennungsdienst hat das Zeitlimit uberschritten.",
    "diagnostic": "Recognition timed out",
    "engine": "trocr",
    "model": "large",
    "page": "folio 1r",
    "scope": "engine/model/page",
    "error_code": "ETIMEDOUT",
    "sanitized_error": "...",
  }

Audit
-----
Call ``audit()`` on any candidate dict to get the canonical ``Status``,
plus a list of fields that contain potentially private data and should
be scrubbed before the record leaves the service boundary.
"""

from __future__ import annotations

import dataclasses
import re
from typing import Literal

# ---------------------------------------------------------------------------
# Core vocabulary
# ---------------------------------------------------------------------------

StatusCode = Literal[
    "success",
    "empty",
    "timeout",
    "unavailable",
    "unsupported_model",
    "backend_error",
    "invalid_response",
    "cancelled",
    "degenerate",
    "missing",
]

RETRYABLE: set[StatusCode] = {
    "timeout",
    "unavailable",
    "backend_error",
    "invalid_response",
    "cancelled",
    "empty",
}

COMPLETE: set[StatusCode] = {
    "success",
    "empty",
    "degenerate",
    "unsupported_model",
    "timeout",
}

# ---------------------------------------------------------------------------
# Human-readable messages (German; matches existing _public_error style)
# ---------------------------------------------------------------------------

PUBLIC_MESSAGES: dict[StatusCode, str] = {
    "success": "Erkennung erfolgreich",
    "empty": "Die Erkennung hat keine Ausgabe erzeugt.",
    "timeout": "Der Erkennungsdienst hat das Zeitlimit überschritten.",
    "unavailable": "Der Erkennungsdienst war nicht erreichbar.",
    "unsupported_model": "Das angeforderte Erkennungsmodell war nicht verfügbar.",
    "backend_error": "Der Erkennungsdienst antwortierte mit einem Fehler.",
    "invalid_response": "Die Antwort des Erkennungsdienstes konnte nicht ausgewertet werden.",
    "cancelled": "Der Erkennungsversuch wurde abgebrochen.",
    "degenerate": "Die Erkennung lieferte keine verwertbare Ausgabe.",
    "missing": "Kein Erkennungsversuch unternommen.",
}

INTERNAL_MESSAGES: dict[StatusCode, str] = {
    "success": "Recognition produced output",
    "empty": "Recognition produced no output",
    "timeout": "Recognition timed out",
    "unavailable": "Recognition service unreachable",
    "unsupported_model": "Requested model not available on this service",
    "backend_error": "Recognition service returned an error",
    "invalid_response": "Recognition response unparseable or malformed",
    "cancelled": "Recognition was cancelled before completion",
    "degenerate": "Output is mechanically degenerate",
    "missing": "No recognition attempted",
}

# ---------------------------------------------------------------------------
# Sanitisation patterns — applied to raw error/diagnostic strings
# ---------------------------------------------------------------------------

SANITIZE_PATTERNS: list[tuple[re.Pattern, str]] = [
    # IP addresses (IPv4 and IPv6)
    (re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}(?::\d+)?"), "[IP]"),
    (re.compile(r"\[[0-9a-fA-F:]+(?::\d+)?\]"), "[IP]"),
    # Tokens / Bearer auth (space, colon or = after keyword)
    (re.compile(r"(?i)(?:Bearer|token|bearer|api[_-]?key)[=:\s]+[^\s\"']+"), "[TOKEN]"),
    # Localhost / internal hostnames — word-boundary anchored
    (re.compile(r"(?i)\b(?:localhost|127\.0\.0\.1|::1)\b"), "[INTERNAL]"),
    # "internal"/"intranet" as standalone words; not subdomains like service.internal
    (re.compile(r"(?i)\b(?:internal|intranet)\b"), "[INTERNAL]"),
    # Stack traces (multi-line including trailing error lines)
    (re.compile(r"Traceback \(most recent call last\):.*?(?=\n\n|\Z)", re.DOTALL), "[STACK TRACE REMOVED]\n"),
    # File paths (absolute Unix and Windows)
    (re.compile(r"(?i)(?:/home/|/var/|/tmp/|[A-Z]:\\(?:Users|Program Files|Windows))[\w./\\-]+"), "[PATH]"),
    # Port numbers attached to hostnames (keep the host)
    (re.compile(r"(?i)(https?://[^\s:]+):\d+(?=/)"), r"\1"),
]

# Fields that may contain credentials or private detail
PRIVATE_FIELDS: set[str] = {
    "token", "bearer", "api_key", "api-key", "apikey",
    "secret", "secret_key", "password", "passwd", "auth", "credential",
    "internal_url", "service_url", "endpoint",
    "request_id", "trace_id", "span_id",
    "raw_response", "debug", "stack", "stacktrace",
}


def _sanitize(value: str) -> str:
    """Remove credentials, IPs, paths, and stack traces from a string."""
    result = str(value)
    for pattern, replacement in SANITIZE_PATTERNS:
        result = pattern.sub(replacement, result)
    return result


# ---------------------------------------------------------------------------
# Normalisation helpers
# ---------------------------------------------------------------------------

# Legacy free-text patterns → status codes (order matters: most specific first)
_LEGACY_PATTERNS: list[tuple[re.Pattern, StatusCode]] = [
    (re.compile(r"(?i)timeout|timed out|Zeitlimit|etimedout"), "timeout"),
    (re.compile(r"(?i)unavailable|nicht erreichbar|connection refused|ECONNREFUSED|ConnectionError|etimedout"), "unavailable"),
    (re.compile(r"(?i)unsupported|not (found|available)|nicht (gefunden|verfugbar)"), "unsupported_model"),
    (re.compile(r"(?i)backend|server error|500|502|503|504|5xx|Internal Server Error"), "backend_error"),
    (re.compile(r"(?i)invalid.*response|unparseable|malformed|could not be parsed"), "invalid_response"),
    (re.compile(r"(?i)cancelled|cancel|abgebrochen|abbruch"), "cancelled"),
]


def _classify_from_error(error: str) -> StatusCode:
    """Infer a status code from a legacy free-text error string."""
    error = str(error or "").strip()
    if not error:
        return "success"
    for pattern, code in _LEGACY_PATTERNS:
        if pattern.search(error):
            return code
    # Unknown free-text error: treat as backend_error (server-side failure).
    # Only numeric 5xx codes are classified as backend_error when the field
    # is explicitly numeric — unknown text strings use the generic message.
    return "backend_error"


def _classify_from_error_code(error_code: str) -> StatusCode | None:
    """Infer a status code from an explicit error_code field value.

    Returns None when the code does not match any known convention,
    allowing the caller to fall through to other classification methods.
    """
    code = str(error_code or "").strip()
    if not code:
        return None
    lowered = code.lower()
    # ETIMEDOUT, ETIMEDOUT, etc. — "timedout" or "timeout" in the code
    if "timedout" in lowered or "timeout" in lowered or code in {"408", "599"}:
        return "timeout"
    # ECONNREFUSED, ECONNRESET, ENOTFOUND, etc.
    if "conn" in lowered or "refused" in lowered or "network" in lowered or code in {"502", "503", "504"}:
        return "unavailable"
    if "unsupported" in lowered or "notfound" in lowered or "not_found" in lowered:
        return "unsupported_model"
    if "cancel" in lowered:
        return "cancelled"
    if code.isdigit():
        return "backend_error"
    return None


def _classify_from_fields(candidate: dict, error_code: str = "") -> StatusCode:
    """Infer status code from structured fields on a candidate dict.

    Resolution order (first match wins):
    1. ``status_code`` or ``status`` field (explicit modern label)
    2. ``error_code`` parameter (numeric or string code from legacy pipeline)
    3. ``error`` field (free-text; classified via patterns)
    4. ``is_degenerate`` flag (from quality pipeline)
    5. ``is_empty`` flag (explicitly set by pipeline)
    6. ``text`` field present-but-empty → ``empty``
    7. No text field and no error → ``missing``
    8. Otherwise → ``success``

    The ``error_code`` parameter bypasses the text check so that an
    explicit timeout/code is never shadowed by a non-empty text field.
    """
    # 1. Explicit status_code / status field
    code = str(candidate.get("status_code") or candidate.get("status") or "").strip().lower()
    if code:
        if code in {"success", "empty", "timeout", "unavailable", "unsupported_model",
                    "backend_error", "invalid_response", "cancelled", "degenerate", "missing"}:
            return code  # type: ignore[return-value]

    # 2. error_code field — backward compatibility for numeric/legacy codes
    #    Common conventions: ETIMEDOUT, ECONNREFUSED, 408, 500, 502, 503, 599
    error_code = str(candidate.get("error_code") or "").strip()
    if error_code:
        error_code_lower = error_code.lower()
        if "timeout" in error_code_lower or error_code in {"408", "599"}:
            return "timeout"
        if "unavailable" in error_code_lower or error_code in {"502", "503", "504", "599"}:
            return "unavailable"
        if "unsupported" in error_code_lower or "notfound" in error_code_lower:
            return "unsupported_model"
        if "cancel" in error_code_lower:
            return "cancelled"
        # Generic server error for any other numeric code
        if error_code.isdigit():
            return "backend_error"

    # 3. Explicit error field — classify from free text
    error = str(candidate.get("error") or "").strip()
    if error:
        return _classify_from_error(error)

    # 4. Degeneracy flags from quality pipeline
    if candidate.get("is_degenerate"):
        return "degenerate"

    # 5. Explicit empty flag
    if candidate.get("is_empty"):
        return "empty"

    # 6. error_code is checked before text to ensure explicit codes are
    #    authoritative (e.g. ETIMEDOUT from a timeout that also has text)
    if error_code:
        code = _classify_from_error_code(error_code)
        if code:
            return code

    # 7. Text field present but empty → empty (distinct from degenerate;
    #    retry may succeed for empty page that just needs more content)
    if "text" in candidate:
        text = str(candidate.get("text") or "").strip()
        if not text:
            return "empty"
        return "success"

    # 8. Neither text field nor error → no recognition was attempted
    return "missing"


# ---------------------------------------------------------------------------
# Main Status dataclass
# ---------------------------------------------------------------------------

@dataclasses.dataclass
class Status:
    """Canonical recognition attempt status with three detail levels.

    Attributes
    ----------
    code : StatusCode
        One of the 10 defined status codes.
    retryable : bool
        True when retrying with the same inputs *might* yield a better result.
    complete : bool
        True when the recognition attempt finished; False when it was
        interrupted before producing any output.
    public_msg : str
        German human-readable message; safe for pages, downloads, API
        responses. Contains no IPs, tokens, paths, or stack traces.
    diagnostic : str
        English message for internal diagnostics; may contain safe
        technical detail.
    engine : str
        Recognition engine name (e.g. "kraken", "trocr", "vlm").
    model : str
        Model identifier within the engine.
    page : str
        Page or folio the recognition was attempted on.
    scope : str
        Granularity of the recognition attempt (e.g. "engine/model/page").
    run_id : str
        Identifier of the pipeline run that produced this attempt.
    timing_ms : int | None
        Recognition wall-clock time in milliseconds, if recorded.
    retry_count : int
        Number of retries required to produce (or fail) this attempt.
    attempt : int
        1-based index of this attempt within the run.
    error_code : str
        Raw error code from the pipeline (from ``error_code`` field), if present.
    raw_error : str
        Unsanitised error string from the pipeline.
    sanitized_error : str
        Error string with credentials, IPs, and paths redacted.
    """
    code: StatusCode
    retryable: bool
    complete: bool
    public_msg: str
    diagnostic: str
    engine: str = ""
    model: str = ""
    page: str = ""
    scope: str = ""
    run_id: str = ""
    timing_ms: int | None = None
    retry_count: int = 0
    attempt: int = 1
    error_code: str = ""
    raw_error: str = ""
    sanitized_error: str = ""

    def to_dict(self) -> dict:
        """Machine-readable status dict with provenance context.

        All fields are safe for public export.``raw_error`` is omitted
        (use ``sanitized_error`` instead).
        """
        result = {
            "status_code": self.code,
            "retryable": self.retryable,
            "complete": self.complete,
            "public_msg": self.public_msg,
            "diagnostic": self.diagnostic,
            "engine": self.engine,
            "model": self.model,
            "page": self.page,
            "scope": self.scope,
            "run_id": self.run_id,
            "timing_ms": self.timing_ms,
            "retry_count": self.retry_count,
            "attempt": self.attempt,
            "error_code": self.error_code,
            "sanitized_error": self.sanitized_error,
        }
        # Omit empty-string fields for cleanliness; preserve False/0 values
        return {k: v for k, v in result.items() if v is not None and v != ""}


def normalize(candidate: dict) -> Status:
    """Convert a raw candidate dict to a canonical ``Status``.

    This is the main entry point for issue #49: given any legacy or current
    candidate shape, return a ``Status`` with safe public messages,
    classified retryability, and provenance context.

    Acceptance criteria
    -------------------
    1. Current timeout and empty-result examples normalise deterministically.
    2. A failed attempt cannot be classified as ``success`` solely because
       confidence is numeric.
    3. All output is safe for public pages and artifacts.
    4. ``error_code`` field is respected when present (backward compat).
    5. Ambiguous records with neither text field nor error normalise to
       ``missing``, not ``success``.
    6. ``to_dict()`` includes engine, model, page, and scope.
    """
    raw_error = str(candidate.get("error") or "").strip()
    sanitized = _sanitize(raw_error)
    error_code = str(candidate.get("error_code") or "").strip()
    code = _classify_from_fields(candidate, error_code=error_code)

    # Extract provenance context from the candidate
    engine = str(candidate.get("engine") or "").strip()
    model = str(candidate.get("model_id") or candidate.get("model") or "").strip()
    page = str(candidate.get("page") or "").strip()
    scope = _scope_label(engine, model, page)

    # Additional run/attempt context fields
    run_id = str(candidate.get("run_id") or "").strip()
    timing_ms_raw = candidate.get("timing_ms")
    timing_ms: int | None = None
    if timing_ms_raw is not None:
        try:
            timing_ms = int(timing_ms_raw)
        except (ValueError, TypeError):
            pass
    retry_count_raw = candidate.get("retry_count", candidate.get("retryCount", 0))
    try:
        retry_count = int(retry_count_raw)
    except (ValueError, TypeError):
        retry_count = 0
    attempt_raw = candidate.get("attempt", 1)
    try:
        attempt = int(attempt_raw)
    except (ValueError, TypeError):
        attempt = 1

    retryable = code in RETRYABLE
    complete = code in COMPLETE or (code not in RETRYABLE and code != "missing")

    return Status(
        code=code,
        retryable=retryable,
        complete=complete,
        public_msg=PUBLIC_MESSAGES.get(code, "Unbekannter Status"),
        diagnostic=INTERNAL_MESSAGES.get(code, "Unknown status"),
        engine=engine,
        model=model,
        page=page,
        scope=scope,
        run_id=run_id,
        timing_ms=timing_ms,
        retry_count=retry_count,
        attempt=attempt,
        error_code=error_code,
        raw_error=raw_error,
        sanitized_error=sanitized,
    )


def _scope_label(engine: str, model: str, page: str) -> str:
    """Human-readable scope label for a recognition attempt."""
    parts = [engine, model, page]
    non_empty = [p for p in parts if p]
    return "/".join(non_empty) if non_empty else "engine"


def audit(candidate: dict) -> tuple[Status, list[str]]:
    """Return canonical Status and list of field names that need sanitisation.

    Use this to audit records before they leave the service boundary.
    ``candidate`` is the raw candidate dict from the pipeline.
    """
    status = normalize(candidate)
    private_fields = [k for k in candidate if k in PRIVATE_FIELDS]
    return status, private_fields


def sanitize_candidate(candidate: dict) -> dict:
    """Return a candidate dict safe for public export.

    Removes or redacts fields listed in ``PRIVATE_FIELDS`` and sanitises
    error strings via ``_sanitize()``.
    """
    public = {}
    for key, value in candidate.items():
        if key in PRIVATE_FIELDS:
            public[key] = "[REDACTED]"
        elif key == "error" and value:
            public[key] = _sanitize(str(value))
        else:
            public[key] = value
    return public


# ---------------------------------------------------------------------------
# Backward-compatibility shim for build_recognitions._public_error
# ---------------------------------------------------------------------------

def public_error_message(error: str | object) -> str:
    """Return a German public message for a raw error value.

    This function replaces ``build_recognitions._public_error`` and
    provides the same interface.  It normalises the error to a Status
    and returns the ``public_msg``.

    Parameters
    ----------
    error : str or object
        A raw error value (string or object with __str__).

    Returns
    -------
    str
        German public message safe for use in HTML; empty string when
        ``error`` is empty/None.
    """
    if error is None:
        return ""
    raw = str(error).strip()
    if not raw:
        return ""
    # Build a minimal candidate dict and normalise it
    cand = {"error": raw}
    status = normalize(cand)
    return status.public_msg