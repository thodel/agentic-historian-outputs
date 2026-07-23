"""Tests for issue #116 — reproducible, data-derived dates.

Running build_outputs on any later day must produce zero drift because all
dates are derived from git-commit metadata, not the wall clock.
"""
from __future__ import annotations

import json
import re
import sys
import unittest
from datetime import date, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

SCRIPTS = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))

import build_outputs  # noqa: E402


def _make_pipeline_json(tmp_path: Path) -> Path:
    """Write a minimal pipeline.json fixture under a doc directory."""
    doc_dir = tmp_path / "doc-test-001"
    doc_dir.mkdir()
    pipeline = doc_dir / "pipeline.json"
    pipeline.write_text(
        json.dumps({
            "transcription": "Test transcription text.",
            "description": {"source_json": {"Sprache": "Latin"}},
            "a_meta": {"review_status": "machine-generated"},
        }),
        encoding="utf-8",
    )
    return pipeline


class TestPipelineDateDerivation(unittest.TestCase):
    """pipeline_date() must derive dates from git, never from datetime.now()."""

    def test_pipeline_date_returns_date_object(self):
        """pipeline_date() must return a datetime.date instance."""
        with patch("build_outputs.subprocess.run") as mock_run:
            # Simulate git returning 2024-03-15T10:00:00+00:00
            mb = MagicMock()
            mb.stdout = "abc1234"
            log = MagicMock()
            log.stdout = "2024-03-15T10:00:00+00:00"
            mock_run.side_effect = [mb, log]
            result = build_outputs.pipeline_date(Path("/fake/pipeline.json"))
        self.assertEqual(result, date(2024, 3, 15))
        self.assertIsInstance(result, date)

    def test_pipeline_date_not_today(self):
        """Returned date must equal git date, not today."""
        today = date.today()
        fixed_past = "2023-01-01T00:00:00+00:00"
        with patch("build_outputs.subprocess.run") as mock_run:
            mb = MagicMock()
            mb.stdout = "abc1234"
            log = MagicMock()
            log.stdout = fixed_past
            mock_run.side_effect = [mb, log]
            result = build_outputs.pipeline_date(Path("/fake/pipeline.json"))
        self.assertEqual(result.year, 2023)
        if today.year >= 2023:
            # The date is NOT the current date (unless we're time-traveling to 2023-01-01)
            self.assertNotEqual(result, today)

    def test_pipeline_date_fallback_to_mtime(self):
        """Without git, pipeline_date() falls back to file mtime."""
        fake_mtime = 1_700_000_000  # 2023-11-14 22:13:20 UTC

        with patch("build_outputs.subprocess.run", side_effect=OSError("no git")):
            with patch.object(Path, "stat") as mock_stat:
                mock_stat.return_value = MagicMock(st_mtime=float(fake_mtime))
                result = build_outputs.pipeline_date(Path("/fake/pipeline.json"))
        import datetime as dt
        expected = dt.datetime.fromtimestamp(fake_mtime, tz=timezone.utc).date()
        self.assertEqual(result, expected)


class TestDateNotFromWallClock(unittest.TestCase):
    """Generated content must not contain today's date when git gives a past date."""

    FIXED_DATE = date(2020, 6, 15)

    def setUp(self):
        import tempfile
        self._tmp = tempfile.mkdtemp()
        self._tmp_path = Path(self._tmp)

    def tearDown(self):
        import shutil
        shutil.rmtree(self._tmp, ignore_errors=True)

    def test_write_tei_uses_provided_date_not_now(self):
        """write_tei() must use doc_date, not datetime.now()."""
        tei_path = self._tmp_path / "transcription.tei.xml"
        build_outputs.write_tei(
            tei_path, "test-doc", "Sample text.", "", doc_date=self.FIXED_DATE
        )
        content = tei_path.read_text(encoding="utf-8")
        self.assertIn('when="2020-06-15"', content)
        # Must NOT contain today's date if it's different from the fixed date
        today_iso = date.today().isoformat()
        if today_iso != self.FIXED_DATE.isoformat():
            self.assertNotIn(f'when="{today_iso}"', content)

    def test_citation_cff_no_datetime_now(self):
        """CITATION.cff date-released must come from pipeline_date(), not now()."""
        # We verify that the pipeline_date() function is called during build_document
        # by checking that the CITATION.cff written does not contain today's date
        # when pipeline_date returns a past date.
        pipeline = self._make_fake_pipeline()
        entity_index: dict = {}

        with patch("build_outputs.pipeline_date", return_value=self.FIXED_DATE):
            with patch("build_outputs.git_history", return_value=[]):
                with patch("build_outputs.DOCS", self._tmp_path):
                    # patch the entity index update to avoid writing to docs/
                    build_outputs.build_document(pipeline, entity_index)

        cff = (pipeline.parent / "CITATION.cff").read_text(encoding="utf-8")
        self.assertIn("date-released: \"2020-06-15\"", cff)
        today_iso = date.today().isoformat()
        if today_iso != self.FIXED_DATE.isoformat():
            self.assertNotIn(f'date-released: "{today_iso}"', cff)

    def test_citation_cff_license_cc_by_40(self):
        """CITATION.cff must use CC-BY-4.0 SPDX identifier."""
        pipeline = self._make_fake_pipeline()
        entity_index: dict = {}

        with patch("build_outputs.pipeline_date", return_value=self.FIXED_DATE):
            with patch("build_outputs.git_history", return_value=[]):
                with patch("build_outputs.DOCS", self._tmp_path):
                    build_outputs.build_document(pipeline, entity_index)

        cff = (pipeline.parent / "CITATION.cff").read_text(encoding="utf-8")
        self.assertIn('license: "CC-BY-4.0"', cff)
        self.assertNotIn("LicenseRef-Not-Specified", cff)

    def _make_fake_pipeline(self) -> Path:
        doc_dir = self._tmp_path / "test-doc"
        doc_dir.mkdir(exist_ok=True)
        pipeline = doc_dir / "pipeline.json"
        pipeline.write_text(
            json.dumps({
                "transcription": "Sample text.",
                "description": {"source_json": {}},
                "a_meta": {"review_status": "machine-generated"},
            }),
            encoding="utf-8",
        )
        return pipeline

    def test_tei_no_datetime_now_in_source(self):
        """No import or call of datetime.now() remains in build_outputs for date generation."""
        source = (SCRIPTS / "build_outputs.py").read_text(encoding="utf-8")
        # datetime.now() must not appear for content generation
        now_calls = re.findall(r"datetime\.now\(\)", source)
        self.assertEqual(
            now_calls, [],
            "datetime.now() found in build_outputs.py — all dates must be data-derived"
        )
