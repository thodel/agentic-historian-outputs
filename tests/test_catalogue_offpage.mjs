// The off-page notice (#253): which index rows it counts, and how it shows them.
import test from "node:test";
import assert from "node:assert/strict";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const { CATALOGUE_DEFAULTS, catalogueFold, catalogueOffPageHits, catalogueRenderOffPage } =
  require("../docs/assets/catalogue.js");

const row = (id, m = {}, q = "") => ({
  id, t: `Titel ${id}`, q: q || `${id.toLowerCase()} brief`,
  m: { documentId: id.toLowerCase(), kind: "output", language: "deutsch", script: "kurrent",
    superseded: "false", recognitionProvenance: "current", recognitionTotal: "2",
    recognitionFailed: "0", recognitionEmpty: "0", recognitionDegenerate: "0",
    recognitionEngines: "kraken", sourceAvailable: "true", sourceType: "image",
    reviewStatus: "machine-generated", comparisonReady: "false", entityTypes: "",
    completeness: "partial", ...m },
});

test("with every filter at its default, every off-page row counts", () => {
  // The old check read `state.language && row.l !== state.language`, and the
  // default is "all": no row ever matched, so the notice never appeared.
  const rows = [row("A-1"), row("A-2")];
  assert.equal(catalogueOffPageHits(rows, new Set(), { ...CATALOGUE_DEFAULTS }).length, 2);
});

test("a filter the off-page check used to ignore now applies", () => {
  const rows = [row("A-1", { reviewStatus: "human-verified" }), row("A-2"),
    row("A-3", { recognitionEngines: "trocr" }), row("A-4", { completeness: "minimal" })];
  const hits = (s) => catalogueOffPageHits(rows, new Set(), { ...CATALOGUE_DEFAULTS, ...s })
    .map(r => r.id);
  assert.deepEqual(hits({ review: "human-verified" }), ["A-1"]);
  assert.deepEqual(hits({ engine: "trocr" }), ["A-3"]);
  assert.deepEqual(hits({ completeness: "minimal" }), ["A-4"]);
});

test("a card on the page is not counted again, whatever the case of its id", () => {
  const onPage = new Set(["a-1"]);             // card datasets carry the folded id
  assert.deepEqual(catalogueOffPageHits([row("A-1"), row("A-2")], onPage,
    { ...CATALOGUE_DEFAULTS }).map(r => r.id), ["A-2"]);
});

test("a query with ß finds a row folded with casefold", () => {
  const rows = [row("A-1", {}, "brief über die strasse")];
  assert.equal(catalogueFold("Straße"), "strasse");
  assert.equal(catalogueOffPageHits(rows, new Set(), { ...CATALOGUE_DEFAULTS, q: "Straße" }).length, 1);
});

function fakeDocument() {
  const make = (tag) => {
    const node = { tag, children: [], textContent: "", href: "" };
    Object.defineProperty(node, "innerHTML", {
      set() { throw new Error("innerHTML must not be used"); },
    });
    return node;
  };
  return { createElement: make, createTextNode: (text) => ({ tag: "#text", textContent: text }) };
}

test("a title is shown as text, never parsed as markup", () => {
  const doc = fakeDocument();
  const target = { replaceChildren(...nodes) { this.nodes = nodes; } };
  Object.defineProperty(target, "innerHTML", { set() { throw new Error("innerHTML used"); } });
  const evil = { ...row("X-1"), t: '<img src=x onerror="alert(1)">' };
  catalogueRenderOffPage(target, [evil, row("X-2")], doc);
  const links = target.nodes.filter(n => n.tag === "a");
  assert.equal(links[0].textContent, '<img src=x onerror="alert(1)">');
  assert.equal(links[0].href, "X-1/");
  assert.equal(target.nodes[0].textContent, "2 weitere Treffer");
});

test("beyond the limit the notice says there are more", () => {
  const target = { replaceChildren(...nodes) { this.nodes = nodes; } };
  const rows = Array.from({ length: 30 }, (_, i) => row(`R-${i}`));
  catalogueRenderOffPage(target, rows, fakeDocument());
  assert.equal(target.nodes.filter(n => n.tag === "a").length, 25);
  assert.equal(target.nodes.at(-1).textContent, " …");
});
