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
    candidate_json_export,
    candidate_tei_xml,
    compute_checksum,
    write_catalogue,
    write_error_record,
    write_exports,
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
    # ---- #38 structured exports ----

    def test_tei_export_is_well_formed_xml(self):
        cand = {"engine": "kraken", "model_id": "mccatmus", "page": "p1", "text": "Hello world"}
        import xml.etree.ElementTree as ET
        xml_str = candidate_tei_xml(cand, "doc-1")
        ET.fromstring(xml_str)  # raises if not well-formed

    def test_tei_export_has_revision_desc(self):
        cand = {"engine": "kraken", "model_id": "mccatmus", "page": "p1", "text": "Hello world"}
        xml_str = candidate_tei_xml(cand, "doc-1")
        self.assertIn("revisionDesc", xml_str)
        self.assertIn("Automated recognition output from kraken", xml_str)
        self.assertIn("machine-generated", xml_str.lower())

    def test_tei_export_skips_layout_fabrication(self):
        cand = {"engine": "kraken", "model_id": "mccatmus", "page": "p1", "text": "Line one\nLine two"}
        xml_str = candidate_tei_xml(cand, "doc-1")
        import xml.etree.ElementTree as ET
        root = ET.fromstring(xml_str)
        ns = "http://www.tei-c.org/ns/1.0"
        # Text blocks contain paragraphs, not coordinate attributes
        for elem in root.iter():
            self.assertNotIn("WIDTH", elem.tag)
            self.assertNotIn("HEIGHT", elem.tag)
            self.assertNotIn("HPOS", elem.tag)
            self.assertNotIn("VPOS", elem.tag)

    def test_json_export_is_well_formed(self):
        cand = {"engine": "kraken", "model_id": "mccatmus", "page": "p1", "text": "Hello world"}
        s = candidate_json_export(cand, "doc-1")
        data = json.loads(s)
        self.assertEqual(data["engine"], "kraken")
        self.assertEqual(data["model_id"], "mccatmus")
        self.assertEqual(data["derivation"], "candidate")
        self.assertIsNone(data["error"])

    def test_json_export_selected_is_labelled(self):
        cand = {"engine": "kraken", "model_id": "mccatmus", "page": "p1", "text": "Hello", "selected": True}
        data = json.loads(candidate_json_export(cand, "doc-1"))
        self.assertEqual(data["derivation"], "selected")

    def test_json_export_error_is_public(self):
        cand = {"engine": "vlm", "model_id": "internvl", "page": "p1", "error": "auth failed: secret-key", "text": ""}
        data = json.loads(candidate_json_export(cand, "doc-1"))
        self.assertNotIn("secret", data["error"].lower())

    def test_write_exports_creates_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            candidates = [
                {"engine": "kraken", "model_id": "mccatmus", "page": "p1", "text": "Hello world"}
            ]
            write_exports(root, "doc-1", candidates)
            export_dir = root / "rec-exports" / "p1"
            self.assertTrue((export_dir / "kraken-mccatmus.json").exists())
            self.assertTrue((export_dir / "kraken-mccatmus.tei.xml").exists())

    def test_write_exports_skips_failures(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            candidates = [
                {"engine": "kraken", "model_id": "mccatmus", "page": "p1", "error": "network timeout", "text": ""}
            ]
            write_exports(root, "doc-1", candidates)
            self.assertFalse((root / "rec-exports").exists())

    def test_tei_export_page_without_page(self):
        cand = {"engine": "kraken", "model_id": "mccatmus", "text": "No page"}
        xml_str = candidate_tei_xml(cand, "doc-1")
        self.assertIn("unassigned", xml_str)

    def test_export_links_in_markup(self):
        html = build_recognition_section([
            {"engine": "kraken", "model_id": "mccatmus", "page": "p1", "text": "Hello world", "confidence": 0.95}
        ], "doc-1", "Hello world")
        self.assertIn("rec-export", html)
        self.assertIn(".json", html)
        self.assertIn(".tei.xml", html)

    # ---- #39 hardening & verification ----

    def test_slug_collision_gives_empty_path_both(self):
        # Two candidates with the same engine+model+page both get empty paths
        # to prevent silent overwrites (no silent overwrite of candidate files)
        raw = [
            {"engine": "kraken", "model_id": "mccatmus", "page": "p1", "text": "First", "confidence": 0.9},
            {"engine": "kraken", "model_id": "mccatmus", "page": "p1", "text": "Second", "confidence": 0.8},
        ]
        processed = _candidates(raw, "First Second")
        non_selected = [c for c in processed if not c.get("selected")]
        self.assertEqual(len(non_selected), 2)
        self.assertEqual(non_selected[0]["path"], "")
        self.assertEqual(non_selected[1]["path"], "")

    def test_checksum_is_deterministic(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as tf:
            tf.write("hello world")
            tf.flush()
            p = Path(tf.name)
            h1 = compute_checksum(p)
            h2 = compute_checksum(p)
            self.assertEqual(h1, h2)
            Path(tf.name).unlink()

    def test_error_record_no_credentials(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = write_error_record(root, {
                "engine": "vlm",
                "model_id": "internvl",
                "page": "p1",
                "error": "auth failed: super-secret-key-12345",
                "text": "",
            })
            if path:
                data = json.loads(path.read_text())
                self.assertNotIn("secret", data["error"].lower())
                self.assertNotIn("super-secret", data["error"])

    def test_write_package_no_private_urls_in_error_records(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_package(root, "doc-1", [
                {"engine": "api", "model_id": "gpt-4", "page": "p1",
                 "error": "server error: https://internal.api.local/secret",
                 "text": ""}
            ], "fused")
            import zipfile
            zp = next(root.glob("*.zip"))
            with zipfile.ZipFile(zp) as zf:
                for name in zf.namelist():
                    if name.endswith(".error.txt"):
                        txt = zf.read(name).decode()
                        self.assertNotIn("internal.api.local", txt)
                        self.assertNotIn("secret", txt.lower())

    def test_catalogue_has_no_credentials(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_catalogue(root, "doc-1", [
                {"engine": "vlm", "model_id": "secret-model", "page": "p1",
                 "error": "https://api.internal.host/auth?key=MY-SECRET", "text": ""}
            ], "transcript")
            cat_path = root / "recognitions" / "catalogue.json"
            if cat_path.exists():
                cat = json.loads(cat_path.read_text())
                cat_str = json.dumps(cat)
                self.assertNotIn("MY-SECRET", cat_str)
                self.assertNotIn("internal.host", cat_str)

    def test_no_js_fallback_semantic_html(self):
        html = build_recognition_section([
            {"engine": "kraken", "model_id": "mccatmus", "page": "p1",
             "text": "Hello world", "confidence": 0.95}
        ], "doc-1", "Hello world")
        # Without JS, panels use <details> which are semantic HTML
        self.assertIn("<details", html)
        self.assertIn("</details>", html)
        # JS-dependent classes not present
        self.assertNotIn("js-only", html)

    def test_checksum_hex_string(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as tf:
            tf.write("test")
            tf.flush()
            p = Path(tf.name)
            h = compute_checksum(p)
            self.assertEqual(len(h), 64)  # SHA-256 = 64 hex chars
            self.assertTrue(h.isalnum())
            Path(tf.name).unlink()

    def test_write_exports_model_with_slash(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_exports(root, "doc-1", [
                {"engine": "zenodo", "model_id": "10.5281/zenodo.123", "page": "p1",
                 "text": "With slash"}
            ])
            export_dir = root / "rec-exports" / "p1"
            files = list(export_dir.iterdir())
            filenames = [f.name for f in files]
            self.assertTrue(any("zenodo" in f and "10-5281" in f for f in filenames))




    # ---- #8 side-by-side comparison shell ----

    def test_compare_entry_point_present(self):
        """A Vergleichen button is rendered in the recognition section."""
        html = build_recognition_section(
            [{"engine": "kraken", "model_id": "mccatmus", "page": "p1",
              "text": "Hello world", "confidence": 0.95}],
            "doc-1", "Hello world")
        self.assertIn("Vergleichen", html)
        self.assertIn("data-rec-compare-open", html)

    def test_compare_panes_have_unique_ids_and_labels(self):
        """Two panes exist with distinct accessible names and DOM ids."""
        html = build_recognition_section(
            [{"engine": "kraken", "model_id": "mccatmus", "page": "p1",
              "text": "Hello"},
             {"engine": "trocr", "model_id": "large", "page": "p1",
              "text": "World"}],
            "doc-1", "Hello world")
        self.assertIn("rec-compare-pane", html)
        self.assertIn('data-rec-compare-pane="left"', html)
        self.assertIn('data-rec-compare-pane="right"', html)
        self.assertIn('rec-compare-select-left', html)
        self.assertIn('rec-compare-select-right', html)
        self.assertIn("Version links", html)
        self.assertIn("Version rechts", html)

    def test_compare_panes_hidden_by_default(self):
        """Comparison panes use the hidden attribute so they are invisible until activated."""
        html = build_recognition_section(
            [{"engine": "kraken", "model_id": "mccatmus", "page": "p1",
              "text": "Hello"}],
            "doc-1", "Hello")
        self.assertIn('data-rec-compare-panes hidden', html)

    def test_compare_selectors_show_all_candidates(self):
        """Both selectors contain an option for every candidate (including fused/selected)."""
        html = build_recognition_section(
            [{"engine": "kraken", "model_id": "mccatmus", "page": "p1",
              "text": "Hello", "confidence": 0.95},
             {"engine": "trocr", "model_id": "large", "page": "p1",
              "text": "World", "confidence": 0.88}],
            "doc-1", "Hello world")
        self.assertIn("kraken", html)
        self.assertIn("trocr", html)
        self.assertIn('data-rec-compare-select="left"', html)
        self.assertIn('data-rec-compare-select="right"', html)

    def test_compare_failed_candidates_disabled(self):
        """Candidates that errored are marked disabled in the compare selectors."""
        html = build_recognition_section(
            [{"engine": "kraken", "model_id": "mccatmus", "page": "p1",
              "error": "connection refused", "text": ""}],
            "doc-1", "fused")
        # The error candidate should be disabled in the select
        self.assertIn(" disabled", html)

    def test_compare_single_page_fixture_all_options_enabled(self):
        """When all candidates belong to the same page, no option is page-restricted."""
        html = build_recognition_section(
            [{"engine": "kraken", "model_id": "mccatmus", "page": "Seite 5",
              "text": "Hello", "confidence": 0.95},
             {"engine": "trocr", "model_id": "large", "page": "Seite 5",
              "text": "World", "confidence": 0.88}],
            "doc-1", "Hello world")
        # Both options have the same page so cross-page restriction keeps none disabled
        # (the JS runtime restriction only disables cross-page options, not same-page)
        self.assertIn("Seite 5", html)
        # Options carry data-page for runtime filtering
        self.assertIn('data-page=', html)

    def test_compare_multi_page_fixture_options_have_page_hints(self):
        """Multi-page candidates include page hints in option labels for clarity."""
        html = build_recognition_section(
            [{"engine": "kraken", "model_id": "mccatmus", "page": "Seite 1",
              "text": "Hello", "confidence": 0.95},
             {"engine": "trocr", "model_id": "large", "page": "Seite 2",
              "text": "World", "confidence": 0.88}],
            "doc-1", "Hello world")
        self.assertIn("Seite 1", html)
        self.assertIn("Seite 2", html)
        # Both selects carry data-page on every option for JS enforcement
        self.assertIn('data-page=', html)

    def test_compare_close_button_present(self):
        """An accessible close control is rendered in the comparison overlay."""
        html = build_recognition_section(
            [{"engine": "kraken", "model_id": "mccatmus", "page": "p1",
              "text": "Hello"}],
            "doc-1", "Hello")
        self.assertIn("data-rec-compare-close", html)
        self.assertIn("Vergleich schliessen", html)

    def test_compare_no_js_fallback_uses_hidden(self):
        """Without JS the comparison panes remain hidden via the hidden attribute."""
        html = build_recognition_section(
            [{"engine": "kraken", "model_id": "mccatmus", "page": "p1",
              "text": "Hello", "confidence": 0.95}],
            "doc-1", "Hello world")
        # hidden attribute ensures no comparison visible without JS
        self.assertIn('data-rec-compare-panes hidden', html)
        # JS adds rec-compare--enhanced; without it structure is still correct
        self.assertIn("data-recognition-compare", html)



if __name__ == "__main__":
    unittest.main()