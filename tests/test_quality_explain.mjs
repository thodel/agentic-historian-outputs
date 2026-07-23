/**
 * test_quality_explain.mjs — Node DOM tests for docs/assets/quality-explain.js
 *
 * Issue #111: wire up .quality-explain-btn click events.
 *
 * Strategy: build a minimal DOM-like context using plain objects, run the
 * script in a vm sandbox, then exercise the exported toggle() / handleClick()
 * helpers and assert that aria-expanded and hidden are updated correctly.
 */
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import vm from "node:vm";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/**
 * Build a minimal fake DOM context and run the shipped asset inside it.
 * Returns the exported { toggle, handleClick } plus the fake document.
 */
function buildContext() {
  const clickListeners = [];

  /** Minimal element stub. */
  function makeElement(id = "", controls = "", initialExpanded = "false") {
    return {
      id,
      _attrs: {
        "aria-controls": controls,
        "aria-expanded": initialExpanded,
      },
      _hidden: true,   // starts hidden (like the real DOM after build)
      classList: { contains: () => false },

      getAttribute(name) { return this._attrs[name] ?? null; },
      setAttribute(name, value) {
        if (name === "hidden") { this._hidden = true; }
        this._attrs[name] = value;
      },
      removeAttribute(name) {
        if (name === "hidden") { this._hidden = false; }
        else { delete this._attrs[name]; }
      },

      closest(selector) {
        // Simulate .closest('.quality-explain-btn') on itself
        if (selector === ".quality-explain-btn" &&
            this.classList._classes &&
            this.classList._classes.includes("quality-explain-btn")) {
          return this;
        }
        return null;
      },
    };
  }

  /** Button stub that has the .quality-explain-btn class. */
  function makeButton(controls, initialExpanded = "false") {
    const btn = makeElement("", controls, initialExpanded);
    btn.classList._classes = ["quality-explain-btn"];
    btn.classList.contains = (cls) => btn.classList._classes.includes(cls);
    btn.closest = (selector) => {
      if (selector === ".quality-explain-btn") return btn;
      return null;
    };
    return btn;
  }

  const elements = {};
  const doc = {
    getElementById(id) { return elements[id] ?? null; },
    addEventListener(type, handler) {
      if (type === "click") clickListeners.push(handler);
    },
  };

  const source = readFileSync(
    new URL("../docs/assets/quality-explain.js", import.meta.url),
    "utf8",
  );

  const ctx = { document: doc, globalThis: {} };
  vm.runInNewContext(source, ctx);

  const { toggle, handleClick } = ctx.globalThis.AgenticQualityExplain;

  return { toggle, handleClick, makeButton, makeElement, elements, clickListeners };
}

// ---------------------------------------------------------------------------
// Tests: toggle()
// ---------------------------------------------------------------------------

test("toggle() reveals a hidden explanation block", () => {
  const { toggle, makeButton, makeElement, elements } = buildContext();
  const block = makeElement("expl-1");
  block._hidden = true;
  elements["expl-1"] = block;

  const btn = makeButton("expl-1", "false");
  toggle(btn);

  assert.equal(btn.getAttribute("aria-expanded"), "true");
  assert.equal(block._hidden, false, "block should no longer be hidden");
});

test("toggle() hides a visible explanation block", () => {
  const { toggle, makeButton, makeElement, elements } = buildContext();
  const block = makeElement("expl-2");
  block._hidden = false;
  elements["expl-2"] = block;

  const btn = makeButton("expl-2", "true");
  toggle(btn);

  assert.equal(btn.getAttribute("aria-expanded"), "false");
  assert.equal(block._hidden, true, "block should be hidden again");
});

test("toggle() is idempotent across two calls (show → hide)", () => {
  const { toggle, makeButton, makeElement, elements } = buildContext();
  const block = makeElement("expl-3");
  block._hidden = true;
  elements["expl-3"] = block;

  const btn = makeButton("expl-3", "false");

  toggle(btn);
  assert.equal(btn.getAttribute("aria-expanded"), "true");
  assert.equal(block._hidden, false);

  toggle(btn);
  assert.equal(btn.getAttribute("aria-expanded"), "false");
  assert.equal(block._hidden, true);
});

test("toggle() is a no-op when aria-controls is missing", () => {
  const { toggle, makeButton } = buildContext();
  const btn = makeButton("" /* no controls */);
  // Should not throw
  toggle(btn);
  assert.equal(btn.getAttribute("aria-expanded"), "false", "aria-expanded unchanged");
});

test("toggle() is a no-op when target element does not exist", () => {
  const { toggle, makeButton } = buildContext();
  const btn = makeButton("nonexistent-id");
  // Should not throw
  toggle(btn);
  assert.equal(btn.getAttribute("aria-expanded"), "false", "aria-expanded unchanged");
});

// ---------------------------------------------------------------------------
// Tests: handleClick() delegation
// ---------------------------------------------------------------------------

test("handleClick() delegates from a child element inside the button", () => {
  const { handleClick, makeButton, makeElement, elements } = buildContext();
  const block = makeElement("expl-delegate");
  block._hidden = true;
  elements["expl-delegate"] = block;

  const btn = makeButton("expl-delegate", "false");

  // Simulate a click on the icon <span> inside the button — event.target is
  // the span, but closest('.quality-explain-btn') should find the button.
  const iconSpan = {
    closest(selector) {
      if (selector === ".quality-explain-btn") return btn;
      return null;
    },
  };
  handleClick({ target: iconSpan });

  assert.equal(btn.getAttribute("aria-expanded"), "true");
  assert.equal(block._hidden, false);
});

test("handleClick() ignores clicks outside .quality-explain-btn", () => {
  const { handleClick } = buildContext();
  let called = false;
  const nonBtn = {
    closest() { return null; },
  };
  // Should be a no-op
  handleClick({ target: nonBtn });
  assert.ok(!called, "nothing should happen for non-button clicks");
});

// ---------------------------------------------------------------------------
// Tests: script registers click listener on document
// ---------------------------------------------------------------------------

test("script attaches a click listener to document on load", () => {
  const { clickListeners } = buildContext();
  assert.equal(clickListeners.length, 1, "exactly one click listener must be registered");
});

// ---------------------------------------------------------------------------
// Tests: aria-expanded reflects state correctly
// ---------------------------------------------------------------------------

test("aria-expanded transitions false → true → false correctly", () => {
  const { toggle, makeButton, makeElement, elements } = buildContext();
  const block = makeElement("expl-states");
  block._hidden = true;
  elements["expl-states"] = block;

  const btn = makeButton("expl-states", "false");

  assert.equal(btn.getAttribute("aria-expanded"), "false");
  toggle(btn);
  assert.equal(btn.getAttribute("aria-expanded"), "true");
  toggle(btn);
  assert.equal(btn.getAttribute("aria-expanded"), "false");
  toggle(btn);
  assert.equal(btn.getAttribute("aria-expanded"), "true");
});
