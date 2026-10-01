"""Links between a training run and the recognitions that used its model (#226).

Every link here is a *relative* URL rendered at a known depth, and the depths
changed under the code when reports moved from one shared index page to a page
per run (#231). Two of them broke silently:

* the raw-record link resolved to ``/training/<run>/<run>/training.json``;
* a recognition backlink resolved to ``/training/<doc_id>/``.

Both still looked plausible in the HTML, which is why asserting on substrings
is not enough. These tests resolve each href the way a browser would, against
the page's real URL, and compare the result to the file the site actually
publishes.

The reverse direction — a recognition naming the run its model came from — did
not exist at all, and a model trained elsewhere was printed as a bare string
with no route to its upstream record.
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import build_recognitions  # noqa: E402
import build_training  # noqa: E402
from training_contract import (  # noqa: E402
    TrainingContract, external_model_url, published_training_runs,
)

SITE = "https://example.test"


def resolve(page_url: str, href: str) -> str:
    """Where a browser lands, following *href* from *page_url*."""
    return urljoin(page_url, href)


def contract(run_id="run-001", model_id="owner/trained-v1"):
    return TrainingContract({
        "schema_version": 1,
        "run_id": run_id,
        "model_id": model_id,
        "base_model": "owner/base-v1",
        "engine": "kraken",
        "created_at": "2026-01-01T00:00:00+00:00",
        "finished_at": "2026-01-02T00:00:00+00:00",
        "epochs": 3,
        "epochs_trained": 3,
        "status": "completed",
        "datasets": [{"hf_repo": "owner/dataset"}],
        "curves": [{"epoch": i, "train_loss": 1.0 - i / 10} for i in range(3)],
    })


class RawRecordLinkTests(unittest.TestCase):
    """The machine-readable record must be reachable from its own page."""

    def test_resolves_to_the_record_beside_the_page(self):
        run = contract()
        html = build_training._render_reproducibility(run)
        href = html.split('<p><a href="')[1].split('"')[0]

        self.assertEqual(
            f"{SITE}/training/run-001/training.json",
            resolve(f"{SITE}/training/run-001/", href),
            "the raw-record link does not resolve to the record published "
            "beside the page",
        )

    def test_does_not_repeat_the_run_id(self):
        href = build_training._render_reproducibility(contract())
        self.assertNotIn("run-001/run-001", href)


class RecognitionBacklinkTests(unittest.TestCase):
    """A run's report links out to the documents that used its model."""

    def test_backlink_resolves_to_the_document(self):
        usages = [{"doc_id": "u-17", "candidate_id": "cand-1",
                   "engine": "kraken", "page": "1", "failed": False}]
        html = build_training._render_recognition_usages("owner/trained-v1", usages)
        href = html.split('<li><a href="')[1].split('"')[0]

        landed = resolve(f"{SITE}/training/run-001/", href)
        self.assertTrue(
            landed.startswith(f"{SITE}/u-17/"),
            f"backlink resolved to {landed}, not to the document page; a "
            "single ../ points at /training/<doc_id>/, which does not exist",
        )
        self.assertIn("rec=cand-1", landed)


class ReverseModelLinkTests(unittest.TestCase):
    """A recognition names the run its model came from, and vice versa."""

    def test_recognition_links_to_the_training_report(self):
        html = build_recognitions._model_provenance_html(
            "owner/trained-v1", {"owner/trained-v1": "run-001"})
        href = html.split('<a href="')[1].split('"')[0]

        self.assertEqual(
            f"{SITE}/training/run-001/",
            resolve(f"{SITE}/u-17/", href),
            "the training link on a document page does not resolve to the run",
        )

    def test_unknown_model_without_upstream_gets_no_link(self):
        html = build_recognitions._model_provenance_html("kraken-local-v1", {})
        self.assertNotIn("<a ", html)
        self.assertIn("kraken-local-v1", html)

    def test_external_model_links_to_its_upstream_record(self):
        html = build_recognitions._model_provenance_html("owner/offtheshelf", {})
        self.assertIn("https://huggingface.co/owner/offtheshelf", html)
        self.assertIn('rel="external"', html)

    def test_a_published_run_wins_over_the_upstream_record(self):
        """Our own report is the better answer when we have one."""
        html = build_recognitions._model_provenance_html(
            "owner/trained-v1", {"owner/trained-v1": "run-001"})
        self.assertIn("../training/run-001/", html)
        self.assertNotIn("huggingface.co", html)


class ExternalModelResolverTests(unittest.TestCase):
    """One resolver, so both sides agree what an identifier points at."""

    def test_hub_repo(self):
        self.assertEqual("https://huggingface.co/owner/name",
                         external_model_url("owner/name"))

    def test_doi_is_not_mistaken_for_a_hub_repo(self):
        """`10.5281/zenodo.1` also satisfies the owner/name shape."""
        self.assertEqual("https://doi.org/10.5281/zenodo.1",
                         external_model_url("10.5281/zenodo.1"))

    def test_bare_name_has_no_upstream(self):
        self.assertEqual("", external_model_url("kraken-medieval-v1"))

    def test_both_renderers_agree(self):
        for model in ("owner/name", "10.5281/zenodo.1", "kraken-local"):
            with self.subTest(model=model):
                base = build_training._base_model_html(model)
                rec = build_recognitions._model_provenance_html(model, {})
                url = external_model_url(model)
                if url:
                    self.assertIn(url, base)
                    self.assertIn(url, rec)
                else:
                    self.assertNotIn("http", base)
                    self.assertNotIn("http", rec)


class PublishedRunIndexTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def _write(self, run_id, payload):
        directory = self.root / "training" / run_id
        directory.mkdir(parents=True)
        (directory / "training.json").write_text(
            json.dumps(payload), encoding="utf-8")

    def test_indexes_model_to_run(self):
        self._write("run-001", {"run_id": "run-001", "model_id": "owner/m"})
        self.assertEqual({"owner/m": "run-001"}, published_training_runs(self.root))

    def test_ignores_a_record_whose_run_id_contradicts_its_directory(self):
        """The id doubles as the URL; a mismatch would link somewhere wrong."""
        self._write("run-001", {"run_id": "somewhere-else", "model_id": "owner/m"})
        self.assertEqual({}, published_training_runs(self.root))

    def test_a_broken_record_costs_only_its_own_link(self):
        directory = self.root / "training" / "run-bad"
        directory.mkdir(parents=True)
        (directory / "training.json").write_text("{not json", encoding="utf-8")
        self._write("run-ok", {"run_id": "run-ok", "model_id": "owner/ok"})

        self.assertEqual({"owner/ok": "run-ok"}, published_training_runs(self.root))


if __name__ == "__main__":
    unittest.main()
