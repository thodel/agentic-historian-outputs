"""Tests for the document slug policy (issue #126)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from build_outputs import (  # noqa: E402
    GRANDFATHERED_SLUGS,
    slug_violation,
    validate_slugs,
)


class SlugViolation(unittest.TestCase):
    def test_valid_ids_have_no_violation(self):
        for doc_id in ("bat", "order-ens", "order-001-group", "u-17",
                       "saa-0001-test", "BAT_664_r_00027", "a", "a1"):
            with self.subTest(doc_id=doc_id):
                self.assertEqual(slug_violation(doc_id), "")

    def test_trailing_separator_is_a_violation(self):
        for doc_id in ("kf-", "u-17__", "abc.", "x_"):
            with self.subTest(doc_id=doc_id):
                self.assertIn("start and end", slug_violation(doc_id))

    def test_leading_separator_is_a_violation(self):
        for doc_id in ("-kf", "_u17", ".hidden"):
            with self.subTest(doc_id=doc_id):
                self.assertIn("start and end", slug_violation(doc_id))

    def test_illegal_character_is_a_violation(self):
        for doc_id in ("hello world", "kf/../etc", "café"):
            with self.subTest(doc_id=doc_id):
                self.assertNotEqual(slug_violation(doc_id), "")


class ValidateSlugs(unittest.TestCase):
    def test_all_valid_passes(self):
        validate_slugs(["bat", "order-ens", "u-17", "BAT_664_r_00027"])

    def test_grandfathered_ids_pass(self):
        # The two ids that predate the policy must not break the build.
        validate_slugs(list(GRANDFATHERED_SLUGS) + ["bat"])

    def test_new_invalid_id_fails_loudly(self):
        with self.assertRaises(SystemExit) as ctx:
            validate_slugs(["bat", "new-run-"])
        message = str(ctx.exception)
        self.assertIn("new-run-", message)
        self.assertIn("supersedes", message)

    def test_current_repository_ids_pass(self):
        doc_ids = [p.parent.name for p in (ROOT / "docs").glob("*/pipeline.json")]
        validate_slugs(doc_ids)


if __name__ == "__main__":
    unittest.main()
