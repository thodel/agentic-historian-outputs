import sys
import tempfile
import unittest
from html.parser import HTMLParser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import json
from build_recognitions import (
    _candidates,
    _confidence,
    _error_path,
    _public_error,
    _recognition_path,
    _safe_slug,
    build_recognition_section,
    compute_checksum,
    write_catalogue,
    write_error_record,
    write_package,
)


class DOM(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.links = []
        self.panels = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get("id"):
            self.ids.append(attrs["id"])
        if tag == "a" and attrs.get("href"):
            self.links.append(attrs["href"])
        if attrs.get("data-recognition-panel"):
            self.panels.append(attrs)


def rec(engine="vlm", model="model", text="text", **extra):
    return {"engine": engine, "model_id": model, "text": text, **extra}


class RecognitionContractTests(unittest.TestCase):
    def test_empty_list_omits_section(self):
        self.assertEqual(build_recognition_section([], "doc", "text"), "")

    def test_selected_output_is_first(self):
        candidates = _candidates([rec()], "fused text")
        self.assertEqual(candidates[0]["id"], "selected")
        self.assertEqual(candidates[0]["text"], "fused text")

    def test_duplicate_ids_are_unique(self):
        candidates = _candidates([rec(), rec()], "fused")
        ids = [c["id"] for c in candidates]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(candidates[1]["path"], "")
        self.assertEqual(candidates[2]["path"], "")

    def test_ids_are_sanitized(self):
        value = _safe_slug('Kraken <script> " model/id')
        self.assertRegex(value, r"^[a-z0-9-]+$")

    def test_page_aware_publisher_path(self):
        candidate = rec("kraken", "10.5281/zenodo.1", page="Page 1.jpg")
        self.assertEqual(
            _recognition_path(candidate),
            "recognitions/Page_1/kraken-10.5281_zenodo.1.txt",
        )

    def test_confidence_is_typed_and_clamped(self):
        self.assertEqual(_confidence(.82), "82%")
        self.assertEqual(_confidence(7), "100%")
        self.assertEqual(_confidence(None), "Nicht angegeben")

    def test_error_messages_hide_internal_details(self):
        raw = "Kraken service error at http://10.0.0.8:8200/ocr: timed out token=secret"
        public = _public_error(raw)
        self.assertIn("Zeitlimit", public)
        self.assertNotIn("10.0.0.8", public)
        self.assertNotIn("secret", public)

    def test_empty_success_becomes_failure(self):
        candidate = _candidates([rec(text="")], "fused")[1]
        self.assertIn("keinen Text", candidate["error"])

    def test_markup_escapes_model_and_text(self):
        markup = build_recognition_section(
            [rec(model='"><script>x</script>', text="<b>raw</b>")], "doc", "fused")
        self.assertNotIn("<script>x</script>", markup)
        self.assertIn("&lt;b&gt;raw&lt;/b&gt;", markup)

    def test_dom_ids_are_unique_and_panels_match_candidates(self):
        markup = build_recognition_section([rec(), rec(), rec("trocr", text="", error="timeout")], "doc", "fused")
        dom = DOM(); dom.feed(markup)
        self.assertEqual(len(dom.ids), len(set(dom.ids)))
        self.assertEqual(len(dom.panels), 4)  # selected + three attempts

    def test_no_js_panels_are_semantic_details(self):
        markup = build_recognition_section([rec(), rec("kraken")], "doc", "fused")
        self.assertEqual(markup.count('<details class="rec-panel"'), 3)
        self.assertIn("<summary>", markup)

    def test_failed_candidate_has_no_download(self):
        markup = build_recognition_section([rec("trocr", text="", error="timeout")], "doc", "fused")
        failed = markup.split('data-recognition-panel="trocr-model"', 1)[1]
        self.assertNotIn("rec-download\" href", failed)
        self.assertIn("Kein Textdownload verfügbar", failed)

    def test_download_only_when_artifact_exists(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "recognitions").mkdir()
            (root / "recognitions" / "fused.txt").write_text("fused")
            markup = build_recognition_section([rec()], "doc", "fused", root)
        self.assertEqual(markup.count("Diese Transkription herunterladen"), 1)
    def test_error_path_replaces_txt_with_error(self):
        cand = {"engine": "kraken", "model_id": "mccatmus", "page": "Page 1.jpg"}
        self.assertEqual(_error_path(cand), "recognitions/Page_1/kraken-mccatmus.error.txt")

    def test_error_path_without_page(self):
        cand = {"engine": "trocr", "model_id": "base"}
        self.assertEqual(_error_path(cand), "recognitions/trocr-base.error.txt")

    def test_write_error_record_creates_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cand = {"engine": "vlm", "model_id": "internvl", "page": "p1",
                    "error": "connection refused"}
            path = write_error_record(root, cand)
            self.assertIsNotNone(path)
            data = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(data["engine"], "vlm")
            self.assertEqual(data["error"], "Der Erkennungsdienst war nicht erreichbar.")

    def test_write_error_record_returns_none_for_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cand = {"engine": "kraken", "model_id": "mccatmus", "text": "some text"}
            self.assertIsNone(write_error_record(root, cand))

    def test_compute_checksum_deterministic(self):
        with tempfile.NamedTemporaryFile(delete=False) as tf:
            tf.write(b"hello world")
            tf.flush()
            p = Path(tf.name)
            c1 = compute_checksum(p)
            c2 = compute_checksum(p)
            self.assertEqual(c1, c2)
            self.assertEqual(len(c1), 64)  # sha256 hex

    def test_write_catalogue_includes_all_candidates(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            recs = [
                {"engine": "kraken", "model_id": "mccatmus", "page": "p1",
                 "text": "hello"},
                {"engine": "vlm", "model_id": "internvl", "page": "p1",
                 "error": "timeout"},
            ]
            path = write_catalogue(root, "doc-1", recs, "fused text")
            data = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(data["doc_id"], "doc-1")
            self.assertEqual(len(data["artifacts"]), 3)  # fused + 2 candidates
            success = next(a for a in data["artifacts"] if a["id"] != "selected")
            self.assertEqual(success["status"], "success")
            self.assertEqual(success["path"], "recognitions/p1/kraken-mccatmus.txt")
            failed = next(a for a in data["artifacts"]
                         if a["status"] == "error")
            self.assertIn("Zeitlimit", failed["error"])
            self.assertIsNone(failed["path"])
            self.assertIsNotNone(failed["error_path"])

    def test_slug_collision_prevention_duplicate_engine_model(self):
        # Two candidates with identical engine+model+page should both have
        # empty paths (ambiguous) to prevent silent overwrites
        recs = [
            {"engine": "kraken", "model_id": "mccatmus", "page": "Page 1.jpg"},
            {"engine": "kraken", "model_id": "mccatmus", "page": "Page 1.jpg"},
        ]
        candidates = _candidates(recs, "fused")
        paths = [c["path"] for c in candidates if not c["selected"]]
        self.assertTrue(all(p == "" for p in paths))

    def test_model_id_slash_becomes_underscore(self):
        cand = {"engine": "vlm", "model_id": "10.5281/zenodo.123", "page": "p1.jpg"}
        self.assertEqual(_recognition_path(cand),
                         "recognitions/p1/vlm-10.5281_zenodo.123.txt")
        # and error path too
        self.assertEqual(_error_path(cand),
                         "recognitions/p1/vlm-10.5281_zenodo.123.error.txt")

    def test_missing_page_no_subdirectory(self):
        cand = {"engine": "trocr", "model_id": "large"}
        self.assertEqual(_recognition_path(cand), "recognitions/trocr-large.txt")

    def test_empty_model_id_omits_model_part(self):
        cand = {"engine": "fusion", "model_id": "", "page": "Page 2"}
        self.assertEqual(_recognition_path(cand), "recognitions/Page_2/fusion.txt")

    def test_fused_txt_path_is_stable(self):
        cand = {"engine": "fusion", "model_id": ""}
        self.assertEqual(_recognition_path(cand), "recognitions/fusion.txt")


    def test_primary_download_appears_in_markup(self):
        markup = build_recognition_section(
            [{"engine": "kraken", "model_id": "mccatmus", "page": "p1", "text": "hello"}],
            "doc", "fused text")
        self.assertIn("Aktuelle Transkription herunterladen", markup)
        self.assertIn("btn-rec-download", markup)
        self.assertIn("data-rec-primary-download", markup)
        self.assertIn("rec-download-format", markup)

    def test_primary_download_unavailable_when_artifact_missing(self):
        markup = build_recognition_section(
            [{"engine": "kraken", "model_id": "mccatmus", "page": "p1", "text": "hello"}],
            "doc", "fused text", directory=Path("/nonexistent"))
        self.assertIn("Kein Textdownload verfügbar", markup)
        self.assertIn("rec-primary-download--unavailable", markup)

    def test_primary_download_provenance_shows_engine_and_page(self):
        markup = build_recognition_section(
            [{"engine": "vlm", "model_id": "internvl", "page": "Seite 50",
              "text": "some text"}],
            "doc", "fused text")
        self.assertIn("vlm", markup)
        self.assertIn("Seite", markup)
        self.assertIn("rec-download-provenance", markup)
    def test_inventory_shows_all_candidates(self):
        markup = build_recognition_section(
            [{"engine": "kraken", "model_id": "mccatmus", "page": "p1", "text": "hello"},
             {"engine": "trocr", "model_id": "large", "page": "p2", "text": "world"}],
            "doc", "fused")
        self.assertIn("rec-inventory", markup)
        self.assertIn("rec-inv-table", markup)
        self.assertIn("p1", markup)
        self.assertIn("p2", markup)
        self.assertIn("kraken", markup)
        self.assertIn("trocr", markup)

    def test_inventory_failed_has_no_download(self):
        # Failed candidates appear as error rows with no text download link
        markup = build_recognition_section(
            [{"engine": "vlm", "model_id": "internvl", "page": "p1",
              "error": "connection refused", "text": ""}],
            "doc", "fused")
        self.assertIn("rec-inv-error", markup)
        # Verify error row has no rec-inv-dl (the "—" placeholder, not a link)
        self.assertIn("Fehlgeschlagen", markup)
        self.assertIn("Der Erkennungsdienst war nicht erreichbar", markup)

    def test_inventory_page_grouping(self):
        # Candidates on same page grouped under one header (selected has no page)
        markup = build_recognition_section(
            [{"engine": "kraken", "model_id": "mccatmus", "page": "Seite 5", "text": "a"},
             {"engine": "trocr", "model_id": "large", "page": "Seite 5", "text": "b"}],
            "doc", "fused")
        self.assertIn("Seite 5", markup)
        # Total version count shown: selected + 2 candidates = 3
        self.assertIn("3 Versionen", markup)

    def test_inventory_collapses_behaves_without_js(self):
        markup = build_recognition_section(
            [{"engine": "kraken", "model_id": "mccatmus", "page": "p1", "text": "hello"}],
            "doc", "fused")
        # No JS required - uses <details>
        self.assertIn("<details class=\"rec-inventory\">", markup)
        self.assertIn("<summary>", markup)
        self.assertIn("</summary>", markup)
        self.assertIn("</details>", markup)
    def test_write_package_creates_zip(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = write_package(root, "doc-1", [
                {"engine": "kraken", "model_id": "mccatmus", "page": "p1", "text": "hello"}
            ], "fused text")
            self.assertIsNotNone(path)
            self.assertTrue(path.exists())
            self.assertTrue(path.name.endswith(".zip"))

    def test_write_package_manifest_has_checksums(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_package(root, "doc-1", [
                {"engine": "kraken", "model_id": "mccatmus", "page": "p1", "text": "hello"}
            ], "fused text")
            import zipfile
            with zipfile.ZipFile(next(root.glob("*.zip"))) as zf:
                manifest = json.loads(zf.read("manifest.json").decode())
                self.assertIn("artifacts", manifest)
                self.assertGreater(len(manifest["artifacts"]), 0)
                for a in manifest["artifacts"]:
                    self.assertIn("checksum", a)

    def test_write_package_includes_fused_and_candidates(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_package(root, "doc-1", [
                {"engine": "kraken", "model_id": "mccatmus", "page": "p1", "text": "hello"}
            ], "fused text")
            import zipfile
            with zipfile.ZipFile(next(root.glob("*.zip"))) as zf:
                names = zf.namelist()
                self.assertIn("fused.txt", names)
                self.assertTrue(any("kraken" in n and n.endswith(".txt") for n in names))

    def test_write_package_error_record_has_no_credentials(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_package(root, "doc-1", [
                {"engine": "vlm", "model_id": "internvl", "page": "p1",
                 "error": "auth failed: my-secret-key", "text": ""}
            ], "fused text")
            import zipfile
            with zipfile.ZipFile(next(root.glob("*.zip"))) as zf:
                err_file = next(n for n in zf.namelist() if n.endswith(".error.txt"))
                err_data = json.loads(zf.read(err_file).decode())
                self.assertNotIn("secret", err_data["error"].lower())
                self.assertNotIn("my-secret", err_data["error"])



if __name__ == "__main__":
    unittest.main()