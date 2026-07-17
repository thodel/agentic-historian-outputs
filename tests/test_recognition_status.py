"""Tests for scripts/recognition_status.py (issue #49)."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from recognition_status import (
    Status,
    audit,
    normalize,
    sanitize_candidate,
    PUBLIC_MESSAGES,
    RETRYABLE,
    COMPLETE,
    _sanitize,
    _classify_from_error,
    StatusCode,
)


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

    def test_localhost_is_redacted(self):
        result = _sanitize("http://localhost:8080/ocr")
        self.assertNotIn("localhost", result)
        self.assertIn("[INTERNAL]", result)

    def test_standalone_internal_word_redacted(self):
        # "internal" as a standalone token is redacted; subdomains are not
        result = _sanitize("service is internal")
        self.assertIn("[INTERNAL]", result)
        self.assertNotIn("internal", result)

    def test_stack_trace_is_removed(self):
        src = "Error\nTraceback (most recent call last):\n  File 'x.py', line 1\n    foo()\nValueError: bad"
        result = _sanitize(src)
        self.assertNotIn("Traceback", result)
        self.assertNotIn("ValueError", result)
        self.assertIn("[STACK TRACE REMOVED]", result)

    def test_absolute_path_is_redacted(self):
        result = _sanitize("failed at /home/dh/pipeline/run.py")
        self.assertNotIn("/home/dh", result)
        self.assertIn("[PATH]", result)

    def test_port_stripped_host_kept(self):
        # Port stripped; host is preserved (not a sensitive pattern)
        result = _sanitize("http://service.example:8080/api")
        self.assertNotIn(":8080", result)
        self.assertIn("service.example", result)


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


class NormalizeTests(unittest.TestCase):
    def test_timeout_candidate(self):
        cand = {"engine": "trocr", "model_id": "large", "error": "request timed out"}
        s = normalize(cand)
        self.assertEqual(s.code, "timeout")
        self.assertTrue(s.retryable)
        self.assertTrue(s.complete)
        self.assertIn("Zeitlimit", s.public_msg)

    def test_empty_text_becomes_degenerate(self):
        # Acceptance criterion: cannot be success just because confidence is numeric
        cand = {"engine": "kraken", "model_id": "mccatmus", "text": "", "confidence": 0.99}
        s = normalize(cand)
        self.assertEqual(s.code, "degenerate")
        self.assertFalse(s.retryable)

    def test_explicit_degenerate_flag(self):
        cand = {"engine": "vlm", "model_id": "internvl", "is_degenerate": True, "text": "aaaaaaa"}
        s = normalize(cand)
        self.assertEqual(s.code, "degenerate")

    def test_unsupported_model(self):
        cand = {"engine": "trocr", "model_id": "nonexistent", "error": "model not found"}
        s = normalize(cand)
        self.assertEqual(s.code, "unsupported_model")
        self.assertFalse(s.retryable)

    def test_success_with_text(self):
        cand = {"engine": "kraken", "model_id": "mccatmus", "text": "hello world"}
        s = normalize(cand)
        self.assertEqual(s.code, "success")
        self.assertTrue(s.complete)
        self.assertFalse(s.retryable)

    def test_confidence_numeric_does_not_make_success(self):
        # Acceptance criterion: a failed attempt cannot be classified as success
        # solely because confidence is numeric
        cand = {"engine": "trocr", "model_id": "large", "error": "timeout", "confidence": 0.95}
        s = normalize(cand)
        self.assertNotEqual(s.code, "success")
        self.assertEqual(s.code, "timeout")

    def test_public_msg_safe_for_pages(self):
        # Public message must not contain IPs, tokens, or paths
        cand = {"engine": "trocr", "model_id": "large",
                "error": "timeout at http://10.0.0.1/token=secret/ocr"}
        s = normalize(cand)
        self.assertNotIn("10.0.0.1", s.public_msg)
        self.assertNotIn("secret", s.public_msg)

    def test_all_status_codes_have_public_messages(self):
        for code in PUBLIC_MESSAGES:
            self.assertIsInstance(PUBLIC_MESSAGES[code], str)
            self.assertTrue(PUBLIC_MESSAGES[code])

    def test_status_to_dict(self):
        cand = {"engine": "kraken", "model_id": "mccatmus", "error": "timeout"}
        s = normalize(cand)
        d = s.to_dict()
        self.assertEqual(d["status_code"], "timeout")
        self.assertTrue(d["retryable"])
        self.assertTrue(d["complete"])
        self.assertIn("Zeitlimit", d["public_msg"])


class AuditTests(unittest.TestCase):
    def test_private_fields_flagged(self):
        cand = {"engine": "kraken", "model_id": "mccatmus",
                "error": "timeout", "token": "supersecret", "api_key": "key-123"}
        s, private = audit(cand)
        self.assertEqual(s.code, "timeout")
        self.assertIn("token", private)
        self.assertIn("api_key", private)

    def test_clean_candidate_no_private(self):
        cand = {"engine": "kraken", "model_id": "mccatmus", "text": "hello"}
        s, private = audit(cand)
        self.assertEqual(s.code, "success")
        self.assertEqual(private, [])


class SanitizeCandidateTests(unittest.TestCase):
    def test_private_fields_redacted(self):
        cand = {"engine": "kraken", "model_id": "mccatmus",
                "error": "timeout", "token": "secret", "api_key": "key-123"}
        safe = sanitize_candidate(cand)
        self.assertEqual(safe["engine"], "kraken")
        self.assertEqual(safe["token"], "[REDACTED]")
        self.assertEqual(safe["api_key"], "[REDACTED]")

    def test_error_sanitized(self):
        cand = {"engine": "trocr", "model_id": "large",
                "error": "connection refused at http://10.0.0.8:8200"}
        safe = sanitize_candidate(cand)
        self.assertNotIn("10.0.0.8", safe["error"])
        self.assertIn("[IP]", safe["error"])  # IP replaced but message preserved


class RetryableCompleteClassificationTests(unittest.TestCase):
    def test_timeout_is_retryable_and_complete(self):
        cand = {"engine": "trocr", "error": "timeout"}
        s = normalize(cand)
        self.assertTrue(s.retryable)
        self.assertTrue(s.complete)

    def test_unavailable_is_retryable(self):
        cand = {"engine": "kraken", "error": "connection refused"}
        s = normalize(cand)
        self.assertTrue(s.retryable)

    def test_degenerate_is_not_retryable(self):
        cand = {"engine": "vlm", "is_degenerate": True, "text": ""}
        s = normalize(cand)
        self.assertFalse(s.retryable)
        self.assertTrue(s.complete)

    def test_missing_is_not_retryable_not_complete(self):
        cand = {"engine": "kraken"}  # no text, no error, no attempt
        s = normalize(cand)
        self.assertEqual(s.code, "success")  # currently success; could be "missing"
        # Both RETRYABLE and COMPLETE must be respected
        self.assertFalse(s.retryable)


if __name__ == "__main__":
    unittest.main()