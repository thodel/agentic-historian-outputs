"""A catalogue may not name a file nobody wrote.

``catalogue.json`` advertised an ``error_path`` for every failed candidate, and
nothing ever wrote the file. All 56 of those references in the published site
pointed at nothing. ``write_error_record`` existed and three tests covered it,
which is why it looked alive: no production code called it.

The content was never lost — ``write_package`` puts the same provenance in the
ZIP under ``candidates/<page>/<id>.error.txt``. But ``catalogue.json`` is a
loose published artifact, and its own ``reuse_notice`` tells a reader to "cite
the failure record with the run provenance". A citation needs an address that
resolves.

So the record is written beside the catalogue now, and the catalogue emits a
path only for a record that was written. The tests below hold both halves: the
files exist, and the two can no longer disagree.

The test that would have caught the original bug is
``test_a_failed_candidate_gets_a_record_on_disk``: it writes a catalogue and
then looks for the file. Grepping the source for a call would have been
brittle; opening the file it promises is not.
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from build_recognitions import (  # noqa: E402
    _candidates, _error_path, write_catalogue, write_error_records,
    write_package,
)


def _failed(engine="trocr", model="kurrent", page="p1.jpg", **extra):
    return {"engine": engine, "model_id": model, "page": page,
            "error": "connection refused", **extra}


def _ok(engine="kraken", model="catmus", page="p1.jpg", text="Hallo Welt"):
    return {"engine": engine, "model_id": model, "page": page, "text": text}


class ErrorRecordTests(unittest.TestCase):

    def test_a_failed_candidate_gets_a_record_on_disk(self):
        """The whole bug in one case: the catalogue promised, nothing wrote."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            catalogue = write_catalogue(root, "doc-1", [_ok(), _failed()], "fused")
            data = json.loads(catalogue.read_text(encoding="utf-8"))
            failed = next(a for a in data["artifacts"] if a["status"] == "error")
            self.assertIsNotNone(
                failed["error_path"],
                "a failed candidate carries no failure record at all",
            )
            self.assertTrue(
                (root / failed["error_path"]).exists(),
                f"catalogue.json names {failed['error_path']}, which does not "
                "exist — this is the defect the module docstring describes",
            )

    def test_every_error_path_in_a_catalogue_resolves(self):
        """The invariant, over a run with several kinds of failure."""
        recognitions = [
            _ok(),
            _failed(engine="trocr", model="a"),
            _failed(engine="vlm", model="b", error="timeout after 30s"),
            {"engine": "kraken", "model_id": "c", "page": "p1.jpg", "text": ""},
        ]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            catalogue = write_catalogue(root, "doc-2", recognitions, "fused")
            data = json.loads(catalogue.read_text(encoding="utf-8"))
            missing = [
                artifact["error_path"] for artifact in data["artifacts"]
                if artifact.get("error_path")
                and not (root / artifact["error_path"]).exists()
            ]
            self.assertEqual([], missing, f"dangling error_path: {missing}")

    def test_a_catalogue_names_no_path_without_a_file(self):
        """Emission is derived from what was written, not from the error flag."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            catalogue = write_catalogue(root, "doc-3", [_failed()], "fused")
            data = json.loads(catalogue.read_text(encoding="utf-8"))
            on_disk = {
                str(path.relative_to(root))
                for path in root.rglob("*.error.txt")
            }
            named = {
                artifact["error_path"] for artifact in data["artifacts"]
                if artifact.get("error_path")
            }
            self.assertEqual(
                named, on_disk,
                "the set of advertised records and the set of written records "
                "differ; they are derived from one mapping so they cannot",
            )

    def test_a_successful_candidate_gets_no_record(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_catalogue(root, "doc-4", [_ok()], "fused")
            self.assertEqual([], list(root.rglob("*.error.txt")))

    def test_an_ambiguous_path_gets_no_loose_record(self):
        """Two attempts that collide on one name identify neither.

        The publisher's path contract has no room for a second candidate from
        the same engine, model and page, and a successful candidate's ``path``
        is already blanked in that case. A record written there would describe
        one attempt under a name that means both, so it is left to the package,
        where the candidate id disambiguates it.
        """
        colliding = [_failed(engine="trocr", model="same"),
                     _failed(engine="trocr", model="same")]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            catalogue = write_catalogue(root, "doc-5", colliding, "fused")
            data = json.loads(catalogue.read_text(encoding="utf-8"))
            paths = [a.get("error_path") for a in data["artifacts"]
                     if a["status"] == "error"]
            self.assertEqual(
                [None, None], paths,
                "an ambiguous name was published as if it identified one "
                "attempt",
            )
            self.assertEqual([], list(root.rglob("*.error.txt")))

    def test_the_record_carries_the_typed_provenance(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_catalogue(root, "doc-6", [_failed()], "fused")
            record = next(root.rglob("*.error.txt"))
            data = json.loads(record.read_text(encoding="utf-8"))
            for field in ("status_code", "retryable", "complete",
                          "diagnostic_code", "error", "engine", "model_id",
                          "page", "reuse_notice"):
                self.assertIn(field, data, f"{field} missing from the record")
            self.assertEqual("unavailable", data["status_code"])
            self.assertEqual(
                "Der Erkennungsdienst war nicht erreichbar.", data["error"])

    def test_the_record_says_to_cite_it(self):
        """The notice is the reason the file has to exist."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_catalogue(root, "doc-7", [_failed()], "fused")
            record = next(root.rglob("*.error.txt"))
            self.assertIn(
                "cite the failure record",
                json.loads(record.read_text(encoding="utf-8"))["reuse_notice"],
            )

    def test_records_are_written_where_the_text_would_have_been(self):
        """Beside the successful candidates, so a failure is addressable too."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            catalogue = write_catalogue(
                root, "doc-8", [_ok(engine="kraken", model="catmus"),
                                _failed(engine="trocr", model="kurrent")],
                "fused")
            data = json.loads(catalogue.read_text(encoding="utf-8"))
            # Not the fused output, which lives at recognitions/fused.txt.
            success = next(a for a in data["artifacts"]
                           if a["status"] == "success" and a["engine"] == "kraken")
            failure = next(a for a in data["artifacts"] if a["status"] == "error")
            self.assertEqual("recognitions/p1/kraken-catmus.txt", success["path"])
            self.assertEqual(
                "recognitions/p1/trocr-kurrent.error.txt", failure["error_path"],
                "a failure record is not beside the texts it stands in for",
            )

    def test_writing_is_idempotent(self):
        """The clean-diff gate requires a rebuild to change nothing."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_catalogue(root, "doc-9", [_failed()], "fused")
            record = next(root.rglob("*.error.txt"))
            first = record.read_bytes()
            write_catalogue(root, "doc-9", [_failed()], "fused")
            self.assertEqual(first, record.read_bytes())

    def test_write_error_records_reports_what_it_wrote(self):
        candidates = _candidates([_ok(), _failed()], "fused")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            written = write_error_records(root, candidates)
            self.assertEqual(1, len(written))
            candidate_id, relative = next(iter(written.items()))
            self.assertEqual(_error_path(
                next(c for c in candidates if c["id"] == candidate_id)),
                relative)
            self.assertTrue((root / relative).exists())


class PackageStillCarriesFailuresTests(unittest.TestCase):
    """The loose record is in addition to the package, not instead of it."""

    def test_the_package_still_holds_its_own_failure_entry(self):
        import zipfile
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package = write_package(root, "doc-10", [_ok(), _failed()], "fused")
            self.assertIsNotNone(package)
            with zipfile.ZipFile(package) as archive:
                names = archive.namelist()
            self.assertTrue(
                any(name.endswith(".error.txt") and name.startswith("candidates/")
                    for name in names),
                f"the package lost its failure entry: {names}",
            )


if __name__ == "__main__":
    unittest.main()
