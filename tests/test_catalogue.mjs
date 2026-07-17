import test from "node:test";
import assert from "node:assert/strict";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const { catalogueMatches, catalogueParams, catalogueStateFromParams } =
  require("../docs/assets/catalogue.js");

const card = {
  search: "doc latin", kind: "output", language: "latin", script: "gothic",
  recognitionEngines: "kraken,trocr", recognitionTotal: "3", recognitionFailed: "1",
  recognitionEmpty: "0", recognitionDegenerate: "0", recognitionProvenance: "current",
  comparisonReady: "true", sourceAvailable: "true", sourceType: "iiif_manifest",
};
const all = { q: "", kind: "all", language: "all", script: "all", engine: "all",
  readiness: "all", failure: "all", source: "all" };

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
