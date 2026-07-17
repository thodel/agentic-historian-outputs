#!/usr/bin/env python3
"""Recognition attempt status taxonomy and sanitisation helpers.

This module provides the canonical status vocabulary for issue #49.

Status codes
------------
Each status is one of:

  success          — recognition produced usable output (text may still be
                     degenerate; see ``degenerate`` status)
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
                       degenerate (repeating characters, empty, or
                       unreasonably long) even though the engine reported
                       no error; retrying will not improve the output
                       without a different engine/model
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
  • ``error_code`` field if present
  • ``status`` field with any legacy label

The ``Status`` dataclass exposes three levels of detail:

  public_msg   — safe for pages, downloads, API responses
  diagnostic   — internal use; may contain safe technical detail
  raw          — original pipeline fields, unsanitised

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
}

COMPLETE: set[StatusCode] = {
    "success",
    "degenerate",
    "unsupported_model",
    "timeout",
}

# ---------------------------------------------------------------------------
# Human-readable messages (German; matches existing _public_error style)
# ---------------------------------------------------------------------------

PUBLIC_MESSAGES: dict[StatusCode, str] = {
    "success": "Erkennung erfolgreich",
    "timeout": "Der Erkennungsdienst hat das Zeitlimit uberschritten.",
    "unavailable": "Der Erkennungsdienst war nicht erreichbar.",
    "unsupported_model": "Das angeforderte Erkennungsmodell war nicht verfugbar.",
    "backend_error": "Der Erkennungsdienst antwortete mit einem Fehler.",
    "invalid_response": "Die Antwort des Erkennungsdienstes konnte nicht ausgewertet werden.",
    "cancelled": "Der Erkennungsversuch wurde abgebrochen.",
    "degenerate": "Die Erkennung lieferte keine verwertbare Ausgabe.",
    "missing": "Kein Erkennungsversuch unternommen.",
}

INTERNAL_MESSAGES: dict[StatusCode, str] = {
    "success": "Recognition produced output",
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
    (re.compile(r"(?i)timeout|timed out|Zeitlimit"), "timeout"),
    (re.compile(r"(?i)unavailable|nicht erreichbar|connection refused|ECONNREFUSED|ConnectionError"), "unavailable"),
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
    # Unknown error: treat as backend_error (something went wrong server-side)
    return "backend_error"


def _classify_from_fields(candidate: dict) -> StatusCode:
    """Infer status code from structured fields on a candidate dict."""
    # Explicit status_code field
    code = str(candidate.get("status_code") or candidate.get("status") or "").strip().lower()
    if code in {"success", "timeout", "unavailable", "unsupported_model",
                "backend_error", "invalid_response", "cancelled", "degenerate", "missing"}:
        return code  # type: ignore[return-value]

    # Explicit error field — classify from free text
    error = str(candidate.get("error") or "").strip()
    if error:
        return _classify_from_error(error)

    # Degeneracy flags set by quality pipeline
    if candidate.get("is_degenerate"):
        return "degenerate"

    # Empty text: only treat as degenerate when a text field was *explicitly*
    # provided (key is present), not when the key is simply absent.
    if "text" in candidate:
        text = str(candidate.get("text") or "").strip()
        if not text:
            return "degenerate"

    return "success"


# ---------------------------------------------------------------------------
# Main Status dataclass
# ---------------------------------------------------------------------------

@dataclasses.dataclass
class Status:
    """Canonical recognition attempt status with three detail levels."""
    code: StatusCode
    retryable: bool
    complete: bool
    public_msg: str
    diagnostic: str
    raw_error: str = ""
    sanitized_error: str = ""

    def to_dict(self) -> dict:
        return {
            "status_code": self.code,
            "retryable": self.retryable,
            "complete": self.complete,
            "public_msg": self.public_msg,
            "diagnostic": self.diagnostic,
        }


def normalize(candidate: dict) -> Status:
    """Convert a raw candidate dict to a canonical ``Status``.

    This is the main entry point for issue #49: given any legacy or current
    candidate shape, return a ``Status`` with safe public messages and
    classified retryability.

    Acceptance criteria
    -------------------
    1. Current timeout and empty-result examples normalise deterministically.
    2. A failed attempt cannot be classified as ``success`` solely because
       confidence is numeric.
    3. All output is safe for public pages and artifacts.
    """
    raw_error = str(candidate.get("error") or "").strip()
    sanitized = _sanitize(raw_error)
    code = _classify_from_fields(candidate)

    retryable = code in RETRYABLE
    complete = code in COMPLETE or (code not in RETRYABLE and code != "missing")

    return Status(
        code=code,
        retryable=retryable,
        complete=complete,
        public_msg=PUBLIC_MESSAGES.get(code, "Unbekannter Status"),
        diagnostic=INTERNAL_MESSAGES.get(code, "Unknown status"),
        raw_error=raw_error,
        sanitized_error=sanitized,
    )


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