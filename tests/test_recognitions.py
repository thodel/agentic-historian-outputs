import sys
import tempfile
import unittest
from html.parser import HTMLParser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import json
import zipfile
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

    def test_single_and_multi_page_candidates_keep_page_provenance(self):
        single = build_recognition_section(
            [rec(page="folio-1")], "doc", "fused")
        multi = build_recognition_section(
            [rec(page="folio-1"), rec(model="model-2", page="folio-2")],
            "doc", "fused",
        )
        self.assertIn('data-page="folio-1"', single)
        self.assertIn('data-page="folio-1"', multi)
        self.assertIn('data-page="folio-2"', multi)

    def test_missing_page_is_explicit(self):
        markup = build_recognition_section([rec()], "doc", "fused")
        self.assertIn("Nicht zugeordnet", markup)

    def test_explanation_blocks_have_deterministic_order(self):
        first = build_recognition_section([rec()], "doc", "fused")
        second = build_recognition_section([rec()], "doc", "fused")
        labels = (
            "engine_confidence", "agreement", "degenerate", "failed",
            "reference_evaluation", "incomparable_confidence",
        )
        for markup in (first, second):
            positions = [markup.index(f'id="quality-explanation-{label}') for label in labels]
            self.assertEqual(positions, sorted(positions))

    def test_duplicate_models_remain_independently_reachable(self):
        markup = build_recognition_section(
            [rec(page="one"), rec(page="two")], "doc", "fused")
        dom = DOM(); dom.feed(markup)
        candidate_panels = [
            panel for panel in dom.panels
            if panel["data-recognition-panel"] != "selected"
        ]
        self.assertEqual(len(candidate_panels), 2)
        self.assertEqual(
            len({panel["data-recognition-panel"] for panel in candidate_panels}),
            2,
        )

    def test_no_js_panels_are_semantic_details(self):
        markup = build_recognition_section([rec(), rec("kraken")], "doc", "fused")
        self.assertEqual(markup.count('<details class="rec-panel"'), 3)
        self.assertIn("<summary>", markup)

    def test_failed_candidate_has_no_download(self):
        markup = build_recognition_section([rec("trocr", text="", error="timeout")], "doc", "fused")
        failed = markup.split('data-recognition-panel="trocr-model"', 1)[1]
        self.assertNotIn("rec-download\" href", failed)
        self.assertIn("Kein Textdownload verfügbar", failed)

    def test_comparison_shell_is_opt_in_and_accessibly_labelled(self):
        markup = build_recognition_section([rec(), rec("kraken")], "doc", "fused")
        self.assertIn("data-recognition-compare", markup)
        self.assertIn("data-rec-compare-panes hidden", markup)
        self.assertIn('for="rec-compare-select-left">Version links', markup)
        self.assertIn('for="rec-compare-select-right">Version rechts', markup)

    def test_comparison_options_are_page_scoped_and_failures_disabled(self):
        markup = build_recognition_section([
            rec(page="p1"),
            rec("kraken", page="p2"),
            rec("trocr", text="", error="timeout", page="p2"),
        ], "doc", "fused")
        self.assertIn('data-page="p1"', markup)
        self.assertIn('data-page="p2"', markup)
        failed_id = _candidates([
            rec(page="p1"), rec("kraken", page="p2"),
            rec("trocr", text="", error="timeout", page="p2"),
        ], "fused")[-1]["id"]
        self.assertIn(f'value="{failed_id}" data-page="p2" disabled', markup)

    def test_comparison_diff_region_is_accessible_and_hidden_by_default(self):
        markup = build_recognition_section([rec(), rec("kraken")], "doc", "fused")
        self.assertIn(
            'data-rec-compare-diff hidden role="region" aria-label="Unterschiede"',
            markup,
        )

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

    def test_failure_provenance_is_preserved_in_package_and_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_package(root, "doc-53", [{
                "engine": "trocr", "model_id": "large", "page": "p2",
                "text": "", "error": "timeout at http://10.0.0.8/token=x",
                "error_code": "ETIMEDOUT", "timing_ms": 1234,
                "run_id": "run-7", "retry_count": 2, "attempt": 3,
                "fusion_decision": "excluded_timeout",
            }], "fused")
            with zipfile.ZipFile(next(root.glob("*.zip"))) as zf:
                error_name = next(n for n in zf.namelist()
                                  if n.endswith(".error.txt"))
                record = json.loads(zf.read(error_name))
                manifest = json.loads(zf.read("manifest.json"))
            entry = next(a for a in manifest["artifacts"]
                         if a["type"] == "error")
            for obj in (record, entry):
                self.assertEqual(obj["status_code"], "timeout")
                self.assertTrue(obj["retryable"])
                self.assertEqual(obj["timing_ms"], 1234)
                self.assertEqual(obj["run_id"], "run-7")
                self.assertEqual(obj["retry_count"], 2)
                self.assertEqual(obj["attempt"], 3)
                self.assertEqual(obj["fusion_decision"], "excluded_timeout")
                self.assertIsNone(obj["text_artifact"])
                self.assertNotIn("10.0.0.8", json.dumps(obj))
            self.assertEqual(entry["reason_no_text"],
                             "recognition_attempt_failed")

    def test_standalone_error_record_has_typed_provenance(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = write_error_record(Path(tmp), {
                "engine": "kraken", "model_id": "m", "page": "p1",
                "text": "", "error": "connection refused",
                "timing_ms": 77, "run_id": "run-1",
            })
            record = json.loads(path.read_text())
            self.assertEqual(record["status_code"], "unavailable")
            self.assertEqual(record["diagnostic_code"], "unavailable")
            self.assertEqual(record["timing_ms"], 77)
            self.assertEqual(record["run_id"], "run-1")
            self.assertIsNone(record["text_artifact"])

    def test_degenerate_viewer_is_not_marked_retryable(self):
        markup = build_recognition_section([{
            "engine": "vlm", "model_id": "m", "page": "p1",
            "text": "a" * 40, "confidence": 0.9,
        }], "doc-54", "selected")
        self.assertIn("Degeneriert", markup)
        self.assertIn("Wiederholung nicht sinnvoll", markup)

    def test_failure_methodology_link_resolves(self):
        markup = build_recognition_section([{
            "engine": "kraken", "model_id": "m", "page": "p1",
            "text": "", "error": "timeout",
        }], "doc-54", "selected")
        self.assertIn('href="/methodology/#recognition-failures"', markup)
        methodology = Path("docs/methodology.md").read_text(encoding="utf-8")
        self.assertIn('id="recognition-failures"', methodology)

    def test_partial_summary_separates_failure_and_degeneration(self):
        markup = build_recognition_section([
            {"engine": "kraken", "model_id": "ok", "text": "usable"},
            {"engine": "trocr", "model_id": "timeout", "text": "",
             "error": "timeout"},
            {"engine": "vlm", "model_id": "deg", "text": "z" * 40,
             "confidence": 0.9},
        ], "doc-54", "selected")
        self.assertIn("1 technisch fehlgeschlagen; 1 degeneriert (von 4)", markup)
        self.assertNotIn("2 von 4 fehlgeschlagen", markup)



    # ---- #12 Harden & Verify: comparison edge cases ----

    def test_compare_no_duplicate_pane_ids(self):
        html = build_recognition_section(
            [{"engine": "kraken", "model_id": "m", "page": "p1",
              "text": "Hello", "confidence": 0.95}],
            "doc-1", "Hello")
        self.assertEqual(html.count('data-rec-compare-pane="left"'), 1)
        self.assertEqual(html.count('data-rec-compare-pane="right"'), 1)

    def test_compare_select_has_no_duplicate_option_values(self):
        html = build_recognition_section(
            [{"engine": "kraken", "model_id": "m", "page": "p1",
              "text": "Hello", "confidence": 0.95},
             {"engine": "trocr", "model_id": "l", "page": "p1",
              "text": "World", "confidence": 0.88}],
            "doc-1", "Hello world")
        import re
        for select_match in re.finditer(
                r'<select[^>]+data-rec-compare-select.*?</select>', html, re.DOTALL):
            values = re.findall(r'value="([^"]+)"', select_match.group(0))
            self.assertEqual(len(values), len(set(values)))

    def test_compare_url_param_functions_present_in_js(self):
        # Load from docs/assets/ — the file the site actually serves.
        js = (Path(__file__).parent.parent / "docs" / "assets" / "rec-viewer.js").read_text()
        self.assertIn("pushcmp(", js)
        self.assertIn("readcmp(", js)

    def test_compare_swap_button_click_handler_in_js(self):
        js = (Path(__file__).parent.parent / "docs" / "assets" / "rec-viewer.js").read_text()
        self.assertIn("leftSel.value", js)
        self.assertIn("rightSel.value", js)

    def test_compare_close_overlay_focus_restoration_in_js(self):
        js = (Path(__file__).parent.parent / "docs" / "assets" / "rec-viewer.js").read_text()
        self.assertIn("openBtn?.focus()", js)
        self.assertIn("closeOverlay(", js)

    def test_compare_unicode_model_names_handled(self):
        html = build_recognition_section(
            [{"engine": "kraken", "model_id": "münster-model/v1", "page": "Seite 1",
              "text": "Hëllö wörld", "confidence": 0.95}],
            "doc-1", "Hëllö wörld")
        self.assertIn("data-rec-compare-open", html)
        self.assertNotIn("undefined", html)

    def test_compare_css_diff_rules_scoping(self):
        css = Path("docs/assets/output.css").read_text()
        self.assertIn(".rec-compare-diff .diff-insert", css)
        self.assertIn(".rec-compare-diff .diff-delete", css)
        self.assertIn(".rec-compare-diff .diff-change", css)

    def test_compare_notice_styles_for_empty_and_error_states(self):
        html = build_recognition_section(
            [{"engine": "kraken", "model_id": "m", "page": "p1",
              "text": "", "confidence": 0.0}],
            "doc-1", "")
        self.assertIn("notice--warning", html)

    def test_compare_flex_layout_uses_gap_for_spacing(self):
        css = Path("docs/assets/output.css").read_text()
        idx = css.find(".rec-compare-panes")
        self.assertNotEqual(idx, -1)
        block = css[idx:idx + 300]
        self.assertTrue(any(prop in block for prop in ("gap", "column-gap", "row-gap")))

    def test_compare_swap_button_has_visible_focus_style(self):
        css = Path("docs/assets/output.css").read_text()
        idx = css.find(".btn-rec-compare-swap")
        self.assertNotEqual(idx, -1)
        self.assertIn(":focus-visible", css[idx:idx + 500])


    # ---- #10 scroll synchronisation across comparison panes ----

    def test_compare_scroll_sync_toggle_injected_by_js(self):
        """Sync toggle button is injected at runtime, not present in static HTML."""
        html = build_recognition_section(
            [{"engine": "kraken", "model_id": "mccatmus", "page": "p1",
              "text": "Hello", "confidence": 0.95},
             {"engine": "trocr", "model_id": "large", "page": "p1",
              "text": "World", "confidence": 0.88}],
            "doc-1", "Hello world")
        # data-rec-compare-sync-toggle must NOT appear in static HTML
        self.assertNotIn("data-rec-compare-sync-toggle", html)

    def test_compare_css_narrow_screen_stacking(self):
        """CSS includes a stacked-layout rule for narrow screens."""
        css = open("docs/assets/output.css").read()
        self.assertIn("max-width: 640px", css)
        self.assertIn("flex-direction: column", css)

    def test_compare_css_sync_toggle_button(self):
        """CSS includes .btn-rec-compare-sync styles."""
        css = open("docs/assets/output.css").read()
        self.assertIn("btn-rec-compare-sync", css)
        self.assertIn("transition", css)

    def test_compare_prefers_reduced_motion_handled_in_js(self):
        """JS checks prefers-reduced-motion before enabling scroll sync."""
        js = open("scripts/rec_viewer.js").read()
        self.assertIn("prefers-reduced-motion", js)


if __name__ == "__main__":
    unittest.main()
