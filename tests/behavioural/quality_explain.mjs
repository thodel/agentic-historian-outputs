/**
 * tests/behavioural/quality_explain.mjs
 *
 * Issue #134: behavioral smoke test for quality-explain toggles.
 *
 * Loads the bat fixture and exercises .quality-explain-btn toggle buttons
 * in a real Chromium DOM via Playwright.
 *
 * A deliberately broken handler (e.g. renamed class) fails CI.
 */

import { chromium } from "playwright";
import { resolve, dirname } from "path";
import test from "node:test";
import { fileURLToPath } from "url";

const __dirname = resolve(dirname(fileURLToPath(import.meta.url)), "..", "..");
const FIXTURE = "file://" + resolve(__dirname, "tests", "behavioural", "fixtures", "bat", "index.html");

// ---------------------------------------------------------------------------
// Helper: launch browser with cached headless Chromium
// ---------------------------------------------------------------------------

async function launchBrowser() {
  const executablePath = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH;
  return chromium.launch({ headless: true, ...(executablePath ? { executablePath } : {}) });
}

// ---------------------------------------------------------------------------
// beforeEach / afterEach setup
// ---------------------------------------------------------------------------

let browser;
let page;

test.beforeEach(async () => {
  browser = await launchBrowser();
  page = await browser.newPage();
  await page.goto(FIXTURE);
  await page.waitForLoadState("domcontentloaded");
  // Scripts are inlined — wait a moment for them to register listeners
  await page.waitForTimeout(200);
});

test.afterEach(async () => {
  if (browser) await browser.close();
});

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

test("quality-explain buttons exist in the DOM", async () => {
  const count = await page.locator(".quality-explain-btn").count();
  if (count < 1) throw new Error("No .quality-explain-btn elements found");
});

test("clicking a collapsed button reveals its target and sets aria-expanded=true", async () => {
  // Use page.evaluate to click and check state to avoid locator staleness
  const result = await page.evaluate(() => {
    const btns = document.querySelectorAll(".quality-explain-btn[aria-expanded='false']");
    if (!btns.length) return { error: "No collapsed buttons" };
    const btn = btns[0];
    const controls = btn.getAttribute("aria-controls");
    if (!controls) return { error: "No aria-controls" };
    const target = document.getElementById(controls);
    if (!target) return { error: "Target not found: " + controls };
    const wasHidden = target.hasAttribute("hidden");
    btn.click();
    return {
      beforeExpanded: btn.getAttribute("aria-expanded"),
      afterExpanded: null, // filled below
      wasHidden,
      targetId: controls,
    };
  });

  if (result.error) throw new Error(result.error);

  // Read state after click (using evaluate again to get current DOM state)
  const after = await page.evaluate((targetId) => {
    const btn = document.querySelector(`.quality-explain-btn[aria-controls='${targetId}']`);
    const target = document.getElementById(targetId);
    return {
      expanded: btn ? btn.getAttribute("aria-expanded") : "btn-not-found",
      targetHidden: target ? target.hasAttribute("hidden") : null,
    };
  }, result.targetId);

  if (after.expanded !== "true") {
    throw new Error(`Expected aria-expanded='true' after click, got '${after.expanded}'`);
  }
  if (after.targetHidden === true) {
    throw new Error(`Target #${result.targetId} should be visible after expanding`);
  }
});

test("clicking an expanded button hides its target and sets aria-expanded=false", async () => {
  // First expand a button via page.evaluate
  const expanded = await page.evaluate(() => {
    const btns = document.querySelectorAll(".quality-explain-btn[aria-expanded='false']");
    if (!btns.length) return null;
    const btn = btns[0];
    const controls = btn.getAttribute("aria-controls");
    if (!controls) return null;
    btn.click();
    return controls;
  });
  if (!expanded) throw new Error("Could not expand a button first");

  // Now collapse it
  const result = await page.evaluate((targetId) => {
    const btn = document.querySelector(`.quality-explain-btn[aria-controls='${targetId}']`);
    if (!btn) return { error: "Button not found" };
    const target = document.getElementById(targetId);
    btn.click();
    return {
      afterExpanded: btn.getAttribute("aria-expanded"),
      targetHidden: target ? target.hasAttribute("hidden") : null,
      targetId,
    };
  }, expanded);

  if (result.error) throw new Error(result.error);
  if (result.afterExpanded !== "false") {
    throw new Error(`Expected aria-expanded='false' after collapse, got '${result.afterExpanded}'`);
  }
  if (result.targetHidden !== true) {
    throw new Error(`Target #${expanded} should be hidden after collapsing`);
  }
});

test("aria-expanded toggles correctly through show→hide→show cycle", async () => {
  const result = await page.evaluate(() => {
    const btn = document.querySelector(".quality-explain-btn");
    if (!btn) return { error: "No button" };
    const states = [];
    for (let i = 0; i < 3; i++) {
      states.push(btn.getAttribute("aria-expanded"));
      btn.click();
    }
    return { states, finalExpanded: btn.getAttribute("aria-expanded") };
  });

  if (result.error) throw new Error(result.error);
  // false → true → false (3 states after 3 clicks starting from initial)
  if (result.states[0] === "false" && result.states[1] === "true" && result.states[2] === "false") {
    // correct cycle
  } else {
    throw new Error(`Unexpected toggle states: ${JSON.stringify(result.states)}`);
  }
});

test("clicking the icon span inside the button also triggers toggle (delegation)", async () => {
  const result = await page.evaluate(() => {
    const icon = document.querySelector(".quality-explain-btn > span[aria-hidden='true']");
    if (!icon) return { error: "No icon span found" };
    const btn = icon.closest(".quality-explain-btn");
    if (!btn) return { error: "Icon not inside button" };
    const controls = btn.getAttribute("aria-controls");
    const beforeExpanded = btn.getAttribute("aria-expanded");
    icon.click();
    return { beforeExpanded, afterExpanded: btn.getAttribute("aria-expanded"), controls };
  });

  if (result.error) throw new Error(result.error);
  if (result.afterExpanded === result.beforeExpanded) {
    throw new Error(
      `Click on icon span did not toggle. Before=${result.beforeExpanded} after=${result.afterExpanded}`
    );
  }
  // Should have toggled
  if (result.beforeExpanded === "false" && result.afterExpanded !== "true") {
    throw new Error(`Expected expansion but got '${result.afterExpanded}'`);
  }
});

test("broken handler: a renamed .quality-explain-btn class fails the test suite", async () => {
  // Verifies the selector actually finds elements
  const count = await page.locator(".quality-explain-btn").count();
  if (count === 0) {
    throw new Error(
      "No .quality-explain-btn buttons found — handler may be broken (class renamed?)"
    );
  }
});

test("multiple buttons toggle independently", async () => {
  const result = await page.evaluate(() => {
    const btns = document.querySelectorAll(".quality-explain-btn");
    if (btns.length < 2) return { skip: true };
    const btn1 = btns[0];
    const btn2 = btns[1];
    const before1 = btn1.getAttribute("aria-expanded");
    const before2 = btn2.getAttribute("aria-expanded");
    btn1.click();
    const after1 = btn1.getAttribute("aria-expanded");
    const after2 = btn2.getAttribute("aria-expanded");
    return { before1, after1, before2, after2 };
  });

  if (result.skip) return; // can't test independence with < 2 buttons

  if (result.after1 === result.before1) {
    throw new Error(`First button did not change (${result.before1} → ${result.after1})`);
  }
  if (result.after2 !== result.before2) {
    throw new Error(
      `Second button changed unexpectedly (${result.before2} → ${result.after2}) — buttons not independent`
    );
  }
});
