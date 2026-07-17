import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import vm from "node:vm";

const source = readFileSync(new URL("../scripts/evidence_viewer.js", import.meta.url), "utf8");
const context = { globalThis: {} };
vm.runInNewContext(source, context);
const { iiifImageUrl } = context.globalThis.AgenticEvidenceViewer;

test("resolves a IIIF Presentation 3 image body", () => {
  const manifest = { items: [{ items: [{ items: [{ body: { id: "https://images.example.org/full.jpg" } }] }] }] };
  assert.equal(iiifImageUrl(manifest), "https://images.example.org/full.jpg");
});

test("resolves a IIIF Presentation 2 image resource", () => {
  const manifest = { sequences: [{ canvases: [{ images: [{ resource: { "@id": "https://images.example.org/v2.jpg" } }] }] }] };
  assert.equal(iiifImageUrl(manifest), "https://images.example.org/v2.jpg");
});

test("uses an image service when no direct body id exists", () => {
  const manifest = { items: [{ items: [{ items: [{ body: { service: [{ id: "https://images.example.org/iiif/1" }] } }] }] }] };
  assert.equal(iiifImageUrl(manifest), "https://images.example.org/iiif/1/full/max/0/default.jpg");
});

test("malformed manifests resolve to an empty fallback", () => {
  assert.equal(iiifImageUrl({}), "");
});
