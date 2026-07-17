import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import vm from "node:vm";

const source = readFileSync(new URL("../scripts/rec_viewer.js", import.meta.url), "utf8");

function fixture(href = "https://example.test/doc/?rec=kraken") {
  const focused = [];
  const listeners = {};
  const pushes = [];

  const panel = (id, page = "") => ({
    id: `recognition-${id}`,
    dataset: { recognitionPanel: id, page },
    hidden: false,
    open: true,
    querySelector: selector => selector === "summary"
      ? { focus: () => focused.push(id) }
      : null,
  });
  const link = id => ({
    dataset: { recognitionSelect: id },
    attrs: {},
    setAttribute(name, value) { this.attrs[name] = value; },
    removeAttribute(name) { delete this.attrs[name]; },
    closest(selector) { return selector === "[data-recognition-select]" ? this : null; },
  });

  const panels = [panel("selected"), panel("kraken", "folio-1")];
  const links = [link("selected"), link("kraken")];
  const viewer = {
    classList: { values: [], add(value) { this.values.push(value); } },
    querySelectorAll(selector) {
      return selector === "[data-recognition-panel]" ? panels : links;
    },
    querySelector() { return null; },
    addEventListener(type, handler) { listeners[type] = handler; },
    dispatchEvent(event) { listeners[event.type]?.(event); return true; },
    contains(value) { return links.includes(value); },
  };
  const context = {
    URL,
    CustomEvent: class CustomEvent {
      constructor(type, options = {}) { this.type = type; this.detail = options.detail; }
    },
    window: { location: { href } },
    document: {
      querySelectorAll(selector) {
        return selector === "[data-recognition-viewer]" ? [viewer] : [];
      },
    },
    history: { pushState(state, unused, url) { pushes.push({ state, url }); } },
    addEventListener(type, handler) { listeners[type] = handler; },
  };
  vm.runInNewContext(source, context);
  return { context, focused, links, listeners, panels, pushes, viewer };
}

test("restores a recognition selection from the URL", () => {
  const state = fixture();
  assert.equal(state.panels[0].hidden, true);
  assert.equal(state.panels[1].hidden, false);
  assert.equal(state.links[1].attrs["aria-current"], "true");
});

test("click selection updates URL, page, focus, and panel state", () => {
  const state = fixture("https://example.test/doc/");
  let prevented = false;
  state.listeners.click({
    target: state.links[1],
    preventDefault() { prevented = true; },
  });
  assert.equal(prevented, true);
  assert.equal(state.panels[1].hidden, false);
  assert.deepEqual(state.focused, ["kraken"]);
  assert.equal(state.pushes.length, 1);
  assert.match(String(state.pushes[0].url), /rec=kraken/);
  assert.match(String(state.pushes[0].url), /page=folio-1/);
  assert.match(String(state.pushes[0].url), /#recognition-kraken$/);
});

test("stale URL selection falls back to selected output", () => {
  const state = fixture("https://example.test/doc/?rec=missing");
  assert.equal(state.panels[0].hidden, false);
  assert.equal(state.links[0].attrs["aria-current"], "true");
});

test("back navigation restores selection without pushing history", () => {
  const state = fixture("https://example.test/doc/");
  state.context.window.location.href = "https://example.test/doc/?rec=kraken";
  state.listeners.popstate();
  assert.equal(state.panels[1].hidden, false);
  assert.equal(state.pushes.length, 0);
});
