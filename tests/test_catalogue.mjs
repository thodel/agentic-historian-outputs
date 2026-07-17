import test from "node:test";
import assert from "node:assert/strict";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const { catalogueCompare, catalogueMatches, catalogueParams, catalogueStateFromParams,
  catalogueStatusText, initCatalogue } =
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

test("invalid fixed URL values degrade to documented defaults", () => {
  const restored = catalogueStateFromParams(new URLSearchParams(
    "kind=unknown&readiness=nope&failure=broken&source=private&sort=random&q=bern"
  ));
  assert.deepEqual(restored, { ...all, q: "bern" });
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

test("empty and populated result messages are explicit", () => {
  assert.equal(catalogueStatusText(1, [], "Dokument-ID: A–Z"),
    "1 Eintrag sichtbar; Sortierung: Dokument-ID: A–Z.");
  assert.equal(catalogueStatusText(0, [["engine", "vlm"]], "Dokument-ID: A–Z"),
    "Keine Einträge entsprechen den aktiven Filtern (vlm).");
});

test("history restoration reapplies filters, card visibility, and empty state", () => {
  const listeners = {};
  const makeControl = (value = "", values = []) => {
    const control = { listeners: {}, options: values.map(item => ({ value: item, textContent: item })) };
    let current = value;
    Object.defineProperty(control, "value", {
      get: () => current,
      set: next => { current = next; control.selectedIndex = Math.max(0, control.options.findIndex(option => option.value === next)); },
    });
    control.value = value;
    control.addEventListener = (event, handler) => { control.listeners[event] = handler; };
    control.dispatch = event => control.listeners[event]?.({ target: control });
    control.appendChild = option => control.options.push(option);
    control.focus = () => { control.focused = true; };
    return control;
  };
  const controls = {
    search: makeControl(""),
    filter: makeControl("all", ["all", "output", "test"]),
    language: makeControl("all", ["all"]), script: makeControl("all", ["all"]),
    engine: makeControl("all", ["all"]),
    readiness: makeControl("all", ["all", "comparison", "candidates", "legacy"]),
    failure: makeControl("all", ["all", "clean", "issues"]),
    source: makeControl("all", ["all", "available", "missing", "iiif_manifest", "image", "landing_page"]),
    sort: makeControl("created-desc", ["created-desc", "created-asc", "title-asc", "title-desc",
      "pages-desc", "pages-asc", "candidates-desc", "candidates-asc", "failures-desc", "failures-asc"]),
  };
  controls.sort.options.forEach(option => { option.textContent = option.value; });
  const clear = makeControl();
  const status = { textContent: "" }; const active = { textContent: "" }; const empty = { hidden: true };
  const cards = [
    { dataset: { ...card, documentId: "issue" }, hidden: false },
    { dataset: { ...card, documentId: "clean", recognitionEngines: "vlm", recognitionFailed: "0" }, hidden: false },
  ];
  const list = { dataset: {}, children: [], appendChild(item) { this.children.push(item); } };
  const nodes = Object.fromEntries(Object.entries(controls).map(([key, value]) => [`#catalogue-${key}`, value]));
  Object.assign(nodes, { "#catalogue-clear": clear, "#catalogue-status": status,
    "#catalogue-active-filters": active, "#catalogue-empty": empty, "#catalogue-list": list });
  const old = { document: global.document, window: global.window, history: global.history,
    addEventListener: global.addEventListener };
  try {
    global.document = {
      querySelector: selector => nodes[selector], querySelectorAll: () => cards,
      createElement: () => ({ value: "", textContent: "" }),
    };
    global.window = { location: new URL("https://example.test/?engine=kraken&failure=issues") };
    global.history = { pushState(_state, _title, url) { global.window.location = new URL(url); } };
    global.addEventListener = (event, handler) => { listeners[event] = handler; };
    initCatalogue();
    assert.deepEqual(cards.map(item => item.hidden), [false, true]);
    assert.equal(empty.hidden, true);

    controls.engine.value = "vlm";
    controls.engine.dispatch("change");
    assert.deepEqual(cards.map(item => item.hidden), [true, true]);
    assert.equal(empty.hidden, false);
    assert.match(status.textContent, /Keine Einträge/);

    global.window.location = new URL("https://example.test/?engine=kraken&failure=issues");
    listeners.popstate();
    assert.equal(controls.engine.value, "kraken");
    assert.deepEqual(cards.map(item => item.hidden), [false, true]);
    assert.equal(empty.hidden, true);
  } finally {
    for (const [key, value] of Object.entries(old)) {
      if (value === undefined) delete global[key]; else global[key] = value;
    }
  }
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
