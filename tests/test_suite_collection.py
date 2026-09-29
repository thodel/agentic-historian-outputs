"""The test suite must not lose tests silently.

CI runs ``python -m unittest discover -s tests``.  That runner only collects
``unittest.TestCase`` subclasses, so a test written in pytest's style — a
module-level ``def test_x()``, or a bare ``class TestX:`` — is skipped without
a word.  Nothing fails, nothing is reported, and the suite looks green.

That is not hypothetical.  Eighty-three cases had accumulated outside the
runner, among them the whole of ``test_rec_artifacts.py`` — forty-five cases
covering artifact path construction, the code that keeps a model id from
escaping its directory.  One of the hidden cases had also silently rotted:
``test_validate_all_mixed`` was building fixtures in a layout the discovery
glob had abandoned, so it asserted against an empty result set and would have
failed the moment anyone looked.

Two guards, because they catch different things:

* the shape check finds tests the runner cannot see, at the point they are
  written;
* the floor catches a module that stops contributing for some other reason —
  an import error swallowed into a ``_FailedTest``, a renamed file, a
  decorator that skips everything.
"""

from __future__ import annotations

import ast
import unittest
from pathlib import Path

TESTS = Path(__file__).resolve().parent

# Raise this when you add tests.  Lower it only deliberately, in the same
# commit that removes them, and say why in the message.
MINIMUM_CASES = 795


def _is_test_case_base(node: ast.expr, local_cases: set[str]) -> bool:
    """Does this base express a unittest.TestCase ancestry?"""
    if isinstance(node, ast.Attribute):          # unittest.TestCase
        return node.attr == "TestCase"
    if isinstance(node, ast.Name):               # TestCase, or a local base
        return node.id == "TestCase" or node.id in local_cases
    return False


def _looks_like_a_test(name: str) -> bool:
    return name.startswith("test_")


class SuiteShapeTests(unittest.TestCase):
    """Every test must be written in a shape the stdlib runner can collect."""

    def _modules(self):
        return sorted(TESTS.glob("test_*.py"))

    def test_no_module_level_test_functions(self):
        offenders = []
        for path in self._modules():
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in tree.body:
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) \
                        and _looks_like_a_test(node.name):
                    offenders.append(f"{path.name}::{node.name}")
        self.assertEqual(
            [], offenders,
            "module-level test functions are invisible to `unittest "
            "discover`; move them into a unittest.TestCase subclass:\n  "
            + "\n  ".join(offenders),
        )

    def test_test_classes_subclass_test_case(self):
        offenders = []
        for path in self._modules():
            tree = ast.parse(path.read_text(encoding="utf-8"))
            local_cases: set[str] = set()
            for node in ast.walk(tree):
                if not isinstance(node, ast.ClassDef):
                    continue
                inherits = any(
                    _is_test_case_base(base, local_cases) for base in node.bases
                )
                if inherits:
                    local_cases.add(node.name)
                    continue
                has_tests = any(
                    isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and _looks_like_a_test(child.name)
                    for child in node.body
                )
                if has_tests:
                    offenders.append(f"{path.name}::{node.name}")
        self.assertEqual(
            [], offenders,
            "these classes hold test methods but do not subclass "
            "unittest.TestCase, so `unittest discover` skips them "
            "silently:\n  " + "\n  ".join(offenders),
        )


class SuiteSizeTests(unittest.TestCase):
    """The runner must keep finding at least as many cases as it did."""

    def _discovered(self):
        loader = unittest.TestLoader()
        suite = loader.discover(start_dir=str(TESTS), top_level_dir=str(TESTS))
        cases = []

        def walk(item):
            if isinstance(item, unittest.TestSuite):
                for child in item:
                    walk(child)
            else:
                cases.append(item)

        walk(suite)
        return cases

    def test_no_module_fails_to_import(self):
        """An unimportable module becomes one _FailedTest, not a loud error."""
        broken = [
            str(case) for case in self._discovered()
            if type(case).__name__ == "_FailedTest"
        ]
        self.assertEqual(
            [], broken,
            "these test modules could not be imported and were replaced by a "
            "single synthetic failure each:\n  " + "\n  ".join(broken),
        )

    def test_suite_has_not_shrunk(self):
        found = len(self._discovered())
        self.assertGreaterEqual(
            found, MINIMUM_CASES,
            f"`unittest discover` now collects {found} cases, below the "
            f"recorded floor of {MINIMUM_CASES}. Tests have gone missing, or "
            "were removed without lowering MINIMUM_CASES in the same commit.",
        )

    def test_every_module_contributes_at_least_one_case(self):
        loader = unittest.TestLoader()
        empty = []
        for path in sorted(TESTS.glob("test_*.py")):
            suite = loader.loadTestsFromName(path.stem)
            if suite.countTestCases() == 0:
                empty.append(path.name)
        self.assertEqual(
            [], empty,
            "these modules are named like tests but contribute no cases to "
            "the stdlib runner:\n  " + "\n  ".join(empty),
        )


if __name__ == "__main__":
    unittest.main()
