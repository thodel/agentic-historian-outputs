import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import vm from "node:vm";

const source = readFileSync(new URL("../scripts/page_sync.js", import.meta.url), "utf8");
const context = { globalThis: {} };
vm.runInNewContext(source, context);
const { chooseCandidate } = context.globalThis.AgenticPageSync;
const link = (page, engine, model) => ({ dataset: { page, engine, model } });

test("preserves engine/model preference across pages", () => {
  const links = [link("p2", "vlm", "a"), link("p2", "kraken", "b")];
  assert.equal(chooseCandidate(links, "p2", { engine: "kraken", model: "b" }), links[1]);
});

test("falls back visibly selectable to first candidate on the page", () => {
  const links = [link("p1", "vlm", "a"), link("p2", "kraken", "b")];
  assert.equal(chooseCandidate(links, "p2", { engine: "missing", model: "x" }), links[1]);
});

test("does not guess across unmatched pages", () => {
  assert.equal(chooseCandidate([link("p1", "vlm", "a")], "p3", {}), null);
});
