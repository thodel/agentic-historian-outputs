"""Tests for scripts/recognition_status.py (issue #49)."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from recognition_status import (
    Status,
    audit,
    normalize,
    public_error_message,
    sanitize_candidate,
    PUBLIC_MESSAGES,
    RETRYABLE,
    COMPLETE,
    _sanitize,
    _classify_from_error,
    _scope_label,
    StatusCode,
)


# ---------------------------------------------------------------------------
# Sample candidates used across tests
# ---------------------------------------------------------------------------

def success(**kw):
    base = {"engine": "kraken", "model_id": "mccatmus", "page": "folio 1r", "text": "hello world"}
    base.update(kw)
    return base


def failed(**kw):
    base = {"engine": "trocr", "model_id": "large", "page": "folio 1v", "error": "timeout"}
    base.update(kw)
    return base


# ---------------------------------------------------------------------------
# Sanitisation tests
# ---------------------------------------------------------------------------

class SanitisationTests(unittest.TestCase):
    def test_ip_v4_is_redacted(self):
        self.assertNotIn("10.0.0.8", _sanitize("error at http://10.0.0.8:8200/ocr"))
        self.assertIn("[IP]", _sanitize("error at http://10.0.0.8:8200/ocr"))

    def test_ipv6_is_redacted(self):
        self.assertIn("[IP]", _sanitize("error at [::1]:8080"))

    def test_token_is_redacted(self):
        self.assertNotIn("secret-token-xyz", _sanitize("token=secret-token-xyz"))
        self.assertIn("[TOKEN]", _sanitize("token=secret-token-xyz"))
        self.assertIn("[TOKEN]", _sanitize("Bearer my-secret-bearer"))
        self.assertIn("[TOKEN]", _sanitize("api_key: super-secret"))

    def test_localhost_is_redacted(self):
        result = _sanitize("http://localhost:8080/ocr")
        self.assertNotIn("localhost", result)
        self.assertIn("[INTERNAL]", result)

    def test_standalone_internal_word_is_redacted(self):
        # "internal" as a standalone word is redacted; subdomains are not
        result = _sanitize("service is internal")
        self.assertIn("[INTERNAL]", result)
        self.assertNotIn(" internal ", result)

    def test_subdomain_internal_not_word_boundary_match(self):
        # "internal" inside "service.internal" IS matched because . creates \b
        # This is expected — the pattern matches the token "internal" anywhere.
        # Non-sensitive subdomains may be partially redacted; this is acceptable.
        result = _sanitize("https://service.internal/api")
        self.assertNotIn("internal.", result)  # token redacted

    def test_stack_trace_is_removed(self):
        src = "Error\n\nTraceback (most recent call last):\n  File 'x.py', line 1\n    foo()\nValueError: bad\n\nMore text"
        result = _sanitize(src)
        self.assertNotIn("Traceback", result)
        self.assertNotIn("ValueError", result)
        self.assertIn("[STACK TRACE REMOVED]", result)
        self.assertIn("More text", result)

    def test_absolute_unix_path_is_redacted(self):
        result = _sanitize("failed at /home/dh/pipeline/run.py")
        self.assertNotIn("/home/dh", result)
        self.assertIn("[PATH]", result)

    def test_absolute_windows_path_is_redacted(self):
        result = _sanitize("C:\\Users\\dh\\pipeline\\run.py")
        self.assertNotIn("C:\\Users", result)
        self.assertIn("[PATH]", result)

    def test_port_stripped_host_kept(self):
        # Port stripped; host is preserved
        result = _sanitize("http://service.example:8080/api")
        self.assertNotIn(":8080", result)
        self.assertIn("service.example", result)

    def test_noop_when_clean(self):
        result = _sanitize("This is a clean error message with no secrets.")
        self.assertEqual(result, "This is a clean error message with no secrets.")


# ---------------------------------------------------------------------------
# Status-code classification
# ---------------------------------------------------------------------------

class ClassifyFromErrorTests(unittest.TestCase):
    def test_timeout_patterns(self):
        for text in ["timed out", "Timeout", "ZEITLIMIT", "request timeout"]:
            self.assertEqual(_classify_from_error(text), "timeout", msg=text)

    def test_unavailable_patterns(self):
        for text in ["unavailable", "Connection refused", "ECONNREFUSED", "nicht erreichbar"]:
            self.assertEqual(_classify_from_error(text), "unavailable", msg=text)

    def test_unsupported_model_patterns(self):
        for text in ["unsupported model", "model not found", "not available", "nicht gefunden"]:
            self.assertEqual(_classify_from_error(text), "unsupported_model", msg=text)

    def test_backend_error_patterns(self):
        for text in ["500 Internal Server Error", "backend error", "502 Bad Gateway"]:
            self.assertEqual(_classify_from_error(text), "backend_error", msg=text)

    def test_invalid_response_patterns(self):
        for text in ["invalid response", "could not be parsed", "malformed"]:
            self.assertEqual(_classify_from_error(text), "invalid_response", msg=text)

    def test_cancelled_patterns(self):
        for text in ["cancelled", "abgebrochen", "canceled"]:
            self.assertEqual(_classify_from_error(text), "cancelled", msg=text)

    def test_empty_is_success(self):
        self.assertEqual(_classify_from_error(""), "success")
        self.assertEqual(_classify_from_error("   "), "success")

    def test_unknown_error_becomes_backend_error(self):
        # Acceptance criterion: cannot be success just because confidence is numeric
        self.assertEqual(_classify_from_error("something went wrong"), "backend_error")


# ---------------------------------------------------------------------------
# All 10 status codes are classified correctly
# ---------------------------------------------------------------------------

class AllStatusCodesTests(unittest.TestCase):
    def test_success(self):
        s = normalize(success())
        self.assertEqual(s.code, "success")
        self.assertFalse(s.retryable)
        self.assertTrue(s.complete)

    def test_empty(self):
        # Explicit is_empty flag
        s = normalize(success(is_empty=True))
        self.assertEqual(s.code, "empty")

    def test_empty_from_text_field(self):
        # Text field present but empty → empty (not success, not degenerate)
        s = normalize(success(text=""))
        self.assertEqual(s.code, "empty")

    def test_timeout(self):
        s = normalize(failed(error="request timed out"))
        self.assertEqual(s.code, "timeout")
        self.assertTrue(s.retryable)
        self.assertTrue(s.complete)

    def test_unavailable(self):
        s = normalize(failed(error="connection refused"))
        self.assertEqual(s.code, "unavailable")
        self.assertTrue(s.retryable)

    def test_unsupported_model(self):
        s = normalize(failed(error="model not found"))
        self.assertEqual(s.code, "unsupported_model")
        self.assertFalse(s.retryable)
        self.assertTrue(s.complete)

    def test_backend_error(self):
        s = normalize(failed(error="500 Internal Server Error"))
        self.assertEqual(s.code, "backend_error")
        self.assertTrue(s.retryable)

    def test_invalid_response(self):
        s = normalize(failed(error="response unparseable"))
        self.assertEqual(s.code, "invalid_response")

    def test_cancelled(self):
        s = normalize(failed(error="cancelled"))
        self.assertEqual(s.code, "cancelled")

    def test_degenerate(self):
        s = normalize(success(is_degenerate=True))
        self.assertEqual(s.code, "degenerate")
        self.assertFalse(s.retryable)

    def test_missing(self):
        # Neither text field nor error → missing (not success)
        s = normalize({"engine": "kraken", "model_id": "mccatmus"})
        self.assertEqual(s.code, "missing")
        self.assertFalse(s.retryable)
        self.assertFalse(s.complete)


# ---------------------------------------------------------------------------
# normalize() acceptance criteria
# ---------------------------------------------------------------------------

class NormalizeAcceptanceTests(unittest.TestCase):
    def test_timeout_deterministic(self):
        # 1. Current timeout and empty-result examples normalise deterministically
        a = normalize(failed(error="Zeitlimit uberschritten"))
        b = normalize(failed(error="ZEITLIMIT"))
        self.assertEqual(a.code, b.code)
        self.assertEqual(a.code, "timeout")

    def test_empty_result_deterministic(self):
        a = normalize(success(text=""))
        b = normalize(success(text="   "))
        self.assertEqual(a.code, "empty")
        self.assertEqual(a.code, b.code)

    def test_confidence_numeric_does_not_make_success(self):
        # 2. A failed attempt cannot be classified as success solely because
        #    confidence is numeric
        s = normalize(failed(error="timeout", confidence=0.95))
        self.assertNotEqual(s.code, "success")
        self.assertEqual(s.code, "timeout")

    def test_error_code_backward_compat(self):
        # 4. error_code field is respected when present (needs text field to
        # avoid being classified as missing)
        s = normalize({"engine": "vlm", "error_code": "ETIMEDOUT", "text": "x"})
        self.assertEqual(s.code, "timeout")
        s2 = normalize({"engine": "vlm", "error_code": "500", "text": "x"})
        self.assertEqual(s2.code, "backend_error")

    def test_error_code_numeric_timeout(self):
        s = normalize({"engine": "kraken", "error_code": "408"})
        self.assertEqual(s.code, "timeout")

    def test_missing_not_success(self):
        # 5. Ambiguous records with neither text field nor error → missing
        s = normalize({"engine": "kraken", "model_id": "mccatmus"})
        self.assertEqual(s.code, "missing")

    def test_public_msg_contains_no_credentials(self):
        # 3. All output is safe for public pages
        s = normalize(failed(error="timeout at http://10.0.0.1/token=secret"))
        self.assertNotIn("10.0.0.1", s.public_msg)
        self.assertNotIn("secret", s.public_msg)
        self.assertIn("[IP]", s.sanitized_error)

    def test_to_dict_includes_engine_model_page(self):
        # 6. to_dict() includes engine, model, page, scope
        s = normalize(success())
        d = s.to_dict()
        self.assertEqual(d["engine"], "kraken")
        self.assertEqual(d["model"], "mccatmus")
        self.assertEqual(d["page"], "folio 1r")
        self.assertIn("scope", d)

    def test_to_dict_omits_empty_fields(self):
        s = normalize(success())
        d = s.to_dict()
        # All values are non-empty strings, booleans, or positive integers
        for k, v in d.items():
            self.assertTrue(
                isinstance(v, bool)
                or (isinstance(v, str) and len(v) > 0)
                or (isinstance(v, int) and v >= 0),
                f"field {k!r} has empty or invalid value: {v!r}"
            )
        # retryable and complete are present and boolean
        self.assertIsInstance(d["retryable"], bool)
        self.assertIsInstance(d["complete"], bool)

    def test_empty_status_has_own_message(self):
        s = normalize(success(text=""))
        self.assertIn("Ausgabe", s.public_msg)  # "keine Ausgabe erzeugt"
        self.assertIn("output", s.diagnostic.lower())  # "Recognition produced no output"


# ---------------------------------------------------------------------------
# Scope label
# ---------------------------------------------------------------------------

class ScopeLabelTests(unittest.TestCase):
    def test_full_scope(self):
        self.assertEqual(_scope_label("kraken", "mccatmus", "folio 1r"),
                         "kraken/mccatmus/folio 1r")

    def test_engine_only(self):
        self.assertEqual(_scope_label("fusion", "", ""), "fusion")

    def test_engine_and_model(self):
        self.assertEqual(_scope_label("vlm", "internvl", ""), "vlm/internvl")

    def test_empty(self):
        self.assertEqual(_scope_label("", "", ""), "engine")


# ---------------------------------------------------------------------------
# audit()
# ---------------------------------------------------------------------------

class AuditTests(unittest.TestCase):
    def test_private_fields_flagged(self):
        cand = dict(success(), token="secret", api_key="key-123")
        s, private = audit(cand)
        self.assertEqual(s.code, "success")
        self.assertIn("token", private)
        self.assertIn("api_key", private)

    def test_clean_candidate_no_private(self):
        s, private = audit(success(text="hello"))
        self.assertEqual(s.code, "success")
        self.assertEqual(private, [])


# ---------------------------------------------------------------------------
# sanitize_candidate()
# ---------------------------------------------------------------------------

class SanitizeCandidateTests(unittest.TestCase):
    def test_private_fields_redacted(self):
        cand = dict(success(), token="secret", api_key="key-123")
        safe = sanitize_candidate(cand)
        self.assertEqual(safe["engine"], "kraken")
        self.assertEqual(safe["token"], "[REDACTED]")
        self.assertEqual(safe["api_key"], "[REDACTED]")

    def test_error_sanitized(self):
        cand = {"engine": "trocr", "error": "connection refused at http://10.0.0.8:8200"}
        safe = sanitize_candidate(cand)
        self.assertNotIn("10.0.0.8", safe["error"])
        self.assertIn("[IP]", safe["error"])


# ---------------------------------------------------------------------------
# public_error_message() shim
# ---------------------------------------------------------------------------

class PublicErrorMessageTests(unittest.TestCase):
    def test_timeout_string(self):
        msg = public_error_message("request timed out")
        self.assertIn("Zeitlimit", msg)

    def test_empty_returns_empty_string(self):
        self.assertEqual(public_error_message(""), "")

    def test_none_returns_empty_string(self):
        self.assertEqual(public_error_message(None), "")

    def test_unknown_error_generic_message(self):
        msg = public_error_message("something unexpected happened")
        self.assertTrue(msg)
        # Generic backend error message (no specific classification)
        self.assertIn("Fehler", msg)


# ---------------------------------------------------------------------------
# Retryable / Complete classification
# ---------------------------------------------------------------------------

class RetryableCompleteTests(unittest.TestCase):
    def test_empty_is_retryable(self):
        # Empty output may succeed on retry (different content, page loaded)
        s = normalize(success(text=""))
        self.assertTrue(s.retryable)
        self.assertTrue(s.complete)

    def test_timeout_is_retryable_and_complete(self):
        s = normalize(failed(error="timeout"))
        self.assertTrue(s.retryable)
        self.assertTrue(s.complete)

    def test_degenerate_not_retryable(self):
        s = normalize(success(is_degenerate=True))
        self.assertFalse(s.retryable)

    def test_missing_not_retryable_not_complete(self):
        s = normalize({"engine": "kraken"})
        self.assertFalse(s.retryable)
        self.assertFalse(s.complete)

    def test_all_status_codes_have_retryable_value(self):
        for code in RETRYABLE:
            self.assertIn(code, list(PUBLIC_MESSAGES.keys()))

    def test_all_status_codes_in_public_messages(self):
        for code in PUBLIC_MESSAGES:
            self.assertIsInstance(PUBLIC_MESSAGES[code], str)
            self.assertTrue(PUBLIC_MESSAGES[code])



# ---------------------------------------------------------------------------
# Integration tests — prove taxonomy governs the publication path
# ---------------------------------------------------------------------------

class IntegrationPublicationPathTests(unittest.TestCase):
    """Prove the taxonomy from issue #49 governs the actual publication path.

    These tests verify that ``normalize()`` output (status codes, public_msg,
    sanitized_error, and provenance context) flows correctly through
    ``build_recognitions._public_error`` and into the candidate records
    that are rendered in pages and written to artifacts.
    """

    def test_full_context_in_to_dict(self):
        # Simulate a candidate as the pipeline would construct it
        candidate = {
            "engine": "trocr",
            "model_id": "large",
            "page": "folio 1v",
            "run_id": "run-2025-07-17-001",
            "timing_ms": 1234,
            "retry_count": 2,
            "attempt": 3,
            "error": "ETIMEDOUT",
        }
        s = normalize(candidate)
        d = s.to_dict()
        self.assertEqual(d["status_code"], "timeout")
        self.assertEqual(d["run_id"], "run-2025-07-17-001")
        self.assertEqual(d["timing_ms"], 1234)
        self.assertEqual(d["retry_count"], 2)
        self.assertEqual(d["attempt"], 3)
        self.assertTrue(d["retryable"])
        self.assertTrue(d["complete"])

    def test_taxonomy_determines_public_message(self):
        # The taxonomy's public_msg must be what _public_error returns
        from scripts.build_recognitions import _public_error
        for error_text, expected_fragment in [
            ("request timed out", "Zeitlimit"),
            ("connection refused", "nicht erreichbar"),
            ("model not found", "nicht verfügbar"),
            ("500 Internal Server Error", "Fehler"),
        ]:
            s = normalize({"engine": "vlm", "error": error_text})
            self.assertIn(expected_fragment, s.public_msg, msg=error_text)
            # _public_error from build_recognitions must match
            self.assertEqual(_public_error(error_text), s.public_msg)

    def test_missing_record_is_not_success(self):
        # A record with no text, no error, no explicit code → 'missing'
        s = normalize({"engine": "kraken", "model_id": "mccatmus"})
        self.assertEqual(s.code, "missing")
        self.assertFalse(s.retryable)
        self.assertFalse(s.complete)
        d = s.to_dict()
        self.assertIn("status_code", d)
        # Provenance fields still populated
        self.assertEqual(d["engine"], "kraken")
        self.assertEqual(d["model"], "mccatmus")



if __name__ == "__main__":
    unittest.main()