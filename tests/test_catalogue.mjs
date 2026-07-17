import test from "node:test";
import assert from "node:assert/strict";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const { catalogueCompare, catalogueMatches, catalogueParams, catalogueStateFromParams } =
  require("../docs/assets/catalogue.js");

const card = {
  search: "doc latin", kind: "output", language: "latin", script: "gothic",
  recognitionEngines: "kraken,trocr", recognitionTotal: "3", recognitionFailed: "1",
  recognitionEmpty: "0", recognitionDegenerate: "0", recognitionProvenance: "current",
  comparisonReady: "true", sourceAvailable: "true", sourceType: "iiif_manifest",
};
const all = { q: "", kind: "all", language: "all", script: "all", engine: "all",
  readiness: "all", failure: "all", source: "all", sort: "created-desc" };

test("provenance filters combine with AND semantics", () => {
  assert.equal(catalogueMatches(card, { ...all, engine: "kraken", readiness: "comparison", failure: "issues", source: "iiif_manifest" }), true);
  assert.equal(catalogueMatches(card, { ...all, engine: "vlm", readiness: "comparison" }), false);
  assert.equal(catalogueMatches(card, { ...all, engine: "kraken", failure: "clean" }), false);
});

test("URL state round trips and omits defaults", () => {
  const state = { ...all, q: "bern", engine: "kraken", readiness: "comparison" };
  const encoded = catalogueParams(state);
  assert.equal(encoded.toString(), "q=bern&engine=kraken&readiness=comparison");
  assert.deepEqual(catalogueStateFromParams(encoded), state);
});

test("legacy records are not silently classified as clean", () => {
  assert.equal(catalogueMatches({ ...card, recognitionProvenance: "legacy", recognitionFailed: "0" }, { ...all, failure: "clean" }), false);
});

test("sorts numeric fields with missing values last and stable document ID ties", () => {
  const cards = [
    { documentId: "doc-10", recognitionPages: "2" },
    { documentId: "doc-2", recognitionPages: "2" },
    { documentId: "unknown", recognitionPages: "" },
    { documentId: "large", recognitionPages: "8" },
  ];
  assert.deepEqual(cards.toSorted((a, b) => catalogueCompare(a, b, "pages-desc")).map(x => x.documentId),
    ["large", "doc-2", "doc-10", "unknown"]);
  assert.deepEqual(cards.toSorted((a, b) => catalogueCompare(a, b, "pages-asc")).map(x => x.documentId),
    ["doc-2", "doc-10", "large", "unknown"]);
});

test("date and title sort directions are explicit and deterministic", () => {
  const cards = [
    { documentId: "b", created: "2025-01-01T00:00:00Z" },
    { documentId: "a", created: "2025-01-01T00:00:00Z" },
    { documentId: "c", created: "2026-01-01T00:00:00Z" },
  ];
  assert.deepEqual(cards.toSorted((a, b) => catalogueCompare(a, b, "created-desc")).map(x => x.documentId), ["c", "a", "b"]);
  assert.deepEqual(cards.toSorted((a, b) => catalogueCompare(a, b, "title-desc")).map(x => x.documentId), ["c", "b", "a"]);
});

test("non-default sort survives URL round trip", () => {
  const state = { ...all, sort: "failures-desc" };
  assert.equal(catalogueParams(state).toString(), "sort=failures-desc");
  assert.deepEqual(catalogueStateFromParams(catalogueParams(state)), state);
});

test("5000-record synthetic catalogue filters and sorts within budget", () => {
  const records = Array.from({ length: 5000 }, (_, index) => ({
    ...card,
    documentId: `doc-${index}`,
    search: `doc-${index} ${index % 2 ? "latin" : "german"}`,
    language: index % 2 ? "latin" : "german",
    recognitionFailed: String(index % 7 === 0 ? 1 : 0),
    recognitionTotal: String((index % 5) + 1),
  }));
  const started = performance.now();
  const matched = records.filter(item => catalogueMatches(item, { ...all, q: "latin" }));
  matched.sort((a, b) => catalogueCompare(a, b, "failures-desc"));
  const elapsed = performance.now() - started;
  assert.equal(matched.length, 2500);
  assert.ok(elapsed < 2000, `interaction took ${elapsed.toFixed(1)}ms`);
});
