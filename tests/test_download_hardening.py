import hashlib
import html
import json
import re
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urlsplit

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from build_recognitions import (
    _candidates,
    build_recognition_section,
    write_package,
)


def recognition(engine="kraken", model="m", page="p1", text="text", **extra):
    return {"engine": engine, "model_id": model, "page": page, "text": text, **extra}


class DownloadHardeningTests(unittest.TestCase):
    def package(self, root, candidates, doc_id="doc-1", transcript="fused"):
        path = write_package(root, doc_id, candidates, transcript)
        self.assertIsNotNone(path)
        return path

    def test_package_is_byte_reproducible_and_manifest_checksums_match(self):
        candidates = [recognition(text="one"), recognition("trocr", "m", "p2", "two")]
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            one = self.package(Path(first), candidates).read_bytes()
            two = self.package(Path(second), candidates).read_bytes()
            self.assertEqual(hashlib.sha256(one).digest(), hashlib.sha256(two).digest())
            with zipfile.ZipFile(Path(first) / "doc-1-recognition-package.zip") as archive:
                manifest = json.loads(archive.read("manifest.json"))
                for artifact in manifest["artifacts"]:
                    self.assertEqual(
                        hashlib.sha256(archive.read(artifact["file"])).hexdigest(),
                        artifact["checksum"],
                    )

    def test_archive_paths_are_unique_relative_and_cover_edge_case_candidates(self):
        candidates = [
            recognition(model="same/model", page="folio 1", text="one"),
            recognition(model="same/model", page="folio 1", text="duplicate"),
            recognition("trocr", "münster/大", None, "unicode"),
            recognition("vlm", "bad", "p3", "", error="token=secret at /tmp/model"),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            path = self.package(Path(tmp), candidates, doc_id="Königsfelden/大")
            with zipfile.ZipFile(path) as archive:
                names = archive.namelist()
                self.assertEqual(len(names), len(set(names)))
                for name in names:
                    posix = PurePosixPath(name)
                    self.assertFalse(posix.is_absolute())
                    self.assertNotIn("..", posix.parts)
                    self.assertNotIn("\\", name)
                candidate_files = [name for name in names if name.startswith("candidates/")]
                self.assertEqual(len(candidate_files), len(candidates))
                self.assertTrue(any(".error.txt" in name for name in candidate_files))

    def test_package_extracts_and_contains_no_private_diagnostics(self):
        candidate = recognition(
            text="", error="FileNotFoundError /home/user/model?token=super-secret",
            api_key="sk-private", internal_url="http://localhost:9000",
        )
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as extracted:
            path = self.package(Path(tmp), [candidate])
            with zipfile.ZipFile(path) as archive:
                archive.extractall(extracted)
            exported = "\n".join(
                item.read_text(encoding="utf-8")
                for item in Path(extracted).rglob("*") if item.is_file()
            )
            for private in ("/home/", "super-secret", "sk-private", "localhost"):
                self.assertNotIn(private, exported)

    def test_every_rendered_download_href_resolves_to_an_emitted_artifact(self):
        raw = [recognition(text="one"), recognition("trocr", "two", "p1", "two")]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            candidates = _candidates(raw, "fused")
            for candidate in candidates:
                if candidate["path"] and not candidate["error"]:
                    target = root / candidate["path"]
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text(candidate["text"], encoding="utf-8")
            markup = build_recognition_section(raw, "doc", "fused", root)
            hrefs = re.findall(r'<a[^>]+href="([^"]+)"[^>]+download', markup)
            self.assertEqual(len(hrefs), 7)  # primary + inventory/panel for three texts
            for href in hrefs:
                relative = unquote(urlsplit(html.unescape(href)).path)
                self.assertTrue((root / relative).is_file(), relative)

    def test_many_candidates_are_not_truncated_in_package_or_inventory(self):
        raw = [recognition(f"engine-{i}", f"model-{i}", f"p{i}", f"text {i}") for i in range(30)]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = self.package(root, raw)
            with zipfile.ZipFile(path) as archive:
                manifest = json.loads(archive.read("manifest.json"))
            self.assertEqual(len(manifest["artifacts"]), 31)  # fused + candidates
            markup = build_recognition_section(raw, "doc", "fused")
            for index in range(30):
                self.assertIn(f"engine-{index}", markup)

    def test_static_download_inventory_is_semantic_without_javascript(self):
        markup = build_recognition_section([recognition()], "doc", "fused")
        self.assertIn('<details class="rec-inventory">', markup)
        self.assertIn("<summary>Alle Erkennungsversionen herunterladen", markup)
        self.assertIn("Aktuelle Transkription herunterladen", markup)
        self.assertIn('<span class="rec-download-format">TXT</span>', markup)
        self.assertNotIn("data-rec-inventory-collapse", markup)


if __name__ == "__main__":
    unittest.main()
