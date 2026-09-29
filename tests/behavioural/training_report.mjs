/**
 * tests/behavioural/training_report.mjs
 *
 * The training report had no browser fixture at all. Two SVGs, the curve
 * provenance notice, the evaluation-kind notice, five disclosures and the
 * exact table were only ever asserted as strings in generated markup, so
 * nothing checked that a reader can actually reach them — or that the report
 * is complete without JavaScript, which is the whole premise of the page.
 *
 * The fixture is rendered from tests/fixtures/training_run_sample.json by
 * tests/generate_training_fixture.py, through the real renderer.
 *
 * Run:
 *   python3 tests/generate_training_fixture.py
 *   node generate-fixtures.mjs
 *   node --test tests/behavioural/training_report.mjs
 */

import { chromium } from "playwright";
import { resolve, dirname } from "path";
import test from "node:test";
import assert from "node:assert";
import { fileURLToPath } from "url";

const __dirname = resolve(dirname(fileURLToPath(import.meta.url)), "..", "..");
const FIXTURE = "file://" + resolve(__dirname, "tests", "behavioural", "fixtures", "training.html");

async function launchBrowser(javaScriptEnabled = true) {
  const executablePath = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH;
  return chromium.launch({ headless: true, ...(executablePath ? { executablePath } : {}) });
}

async function open({ javaScriptEnabled = true } = {}) {
  const browser = await launchBrowser();
  const context = await browser.newContext({ javaScriptEnabled });
  const page = await context.newPage();
  await page.goto(FIXTURE);
  await page.waitForLoadState("domcontentloaded");
  return { browser, page };
}

// ---------------------------------------------------------------------------
// The charts a reader is meant to look at
// ---------------------------------------------------------------------------

test("both curves render as labelled, accessible SVG", async () => {
  const { browser, page } = await open();
  try {
    const charts = page.locator("figure.training-chart svg");
    assert.strictEqual(await charts.count(), 2, "expected a loss and an accuracy chart");

    for (let i = 0; i < 2; i++) {
      const svg = charts.nth(i);
      assert.strictEqual(await svg.getAttribute("role"), "img");
      const labelledBy = await svg.getAttribute("aria-labelledby");
      assert.ok(labelledBy, "chart has no accessible name");
      for (const id of labelledBy.split(/\s+/)) {
        assert.strictEqual(
          await page.locator(`[id="${id}"]`).count(), 1,
          `aria-labelledby points at #${id}, which does not exist`,
        );
      }
      assert.ok(await svg.locator("polyline").count() > 0, "chart drew no line");
    }
  } finally {
    await browser.close();
  }
});

test("charts have non-zero rendered size", async () => {
  const { browser, page } = await open();
  try {
    const box = await page.locator("figure.training-chart svg").first().boundingBox();
    assert.ok(box && box.width > 200 && box.height > 80,
      `chart rendered at ${JSON.stringify(box)} — it is present in the DOM but not visible`);
  } finally {
    await browser.close();
  }
});

// ---------------------------------------------------------------------------
// The claims the page makes about its own data
// ---------------------------------------------------------------------------

test("an incomplete curve is marked as a selection, in the open", async () => {
  const { browser, page } = await open();
  try {
    const notice = page.locator(".training-curve-provenance");
    assert.strictEqual(await notice.count(), 1);
    assert.ok(await notice.isVisible(), "the curve provenance notice is hidden");
    const text = await notice.innerText();
    assert.match(text, /Unvollständige Kurve/,
      "a curve built from the ten best checkpoints is not marked as a selection");
    assert.match(text, /top 10 checkpoints/, "the notice does not say what was kept");
  } finally {
    await browser.close();
  }
});

test("the evaluation kind is stated where the metrics are", async () => {
  const { browser, page } = await open();
  try {
    await page.locator("summary", { hasText: "Validierungsmetriken" }).click();
    const kind = page.locator("[data-evaluation-kind]");
    assert.strictEqual(await kind.getAttribute("data-evaluation-kind"), "line_crop");
    assert.match(await kind.innerText(), /Zeilenausschnitte/);
  } finally {
    await browser.close();
  }
});

// ---------------------------------------------------------------------------
// Navigation out of the report
// ---------------------------------------------------------------------------

test("the raw record link points beside the page, not one level deeper", async () => {
  const { browser, page } = await open();
  try {
    await page.locator("summary", { hasText: "Reproduzierbarkeit" }).click();
    const href = await page.locator('a[href$="training.json"]').first().getAttribute("href");
    assert.strictEqual(href, "training.json",
      `raw record link is ${href}; from /training/<run>/ that resolves one level too deep`);
  } finally {
    await browser.close();
  }
});

test("recognition backlinks climb two levels to the document", async () => {
  const { browser, page } = await open();
  try {
    await page.locator("summary", { hasText: "Verwendungen" }).click();
    const links = page.locator(".training-model-usages a");
    assert.ok(await links.count() >= 1, "no recognition backlinks rendered");
    const href = await links.first().getAttribute("href");
    assert.ok(href.startsWith("../../"),
      `backlink is ${href}; a single ../ resolves to /training/<doc_id>/`);
  } finally {
    await browser.close();
  }
});

// ---------------------------------------------------------------------------
// The premise of the page
// ---------------------------------------------------------------------------

test("the report is complete without JavaScript", async () => {
  const { browser, page } = await open({ javaScriptEnabled: false });
  try {
    assert.strictEqual(await page.locator("figure.training-chart svg").count(), 2,
      "curves are missing without JavaScript");
    assert.ok(await page.locator(".training-curve-provenance").isVisible(),
      "the curve provenance notice needs JavaScript to appear");

    // <details> toggles without scripting, so every panel is reachable. The
    // curves panel ships open, so assert reachability by toggling to a known
    // state rather than by clicking once and hoping it was closed.
    for (const label of ["Trainingskurven", "Datensatzprovenienz",
                         "Reproduzierbarkeit", "Verwendungen", "Validierungsmetriken"]) {
      const summary = page.locator("summary", { hasText: label });
      assert.strictEqual(await summary.count(), 1, `no panel for ${label}`);
      const wasOpen = await summary.evaluate(node => node.parentElement.open);
      await summary.click();
      assert.strictEqual(
        await summary.evaluate(node => node.parentElement.open), !wasOpen,
        `${label} did not toggle without JavaScript`,
      );
      if (wasOpen) await summary.click();
      assert.ok(await summary.evaluate(node => node.parentElement.open),
        `${label} cannot be opened without JavaScript`);
    }
  } finally {
    await browser.close();
  }
});

test("the exact epoch table is reachable and holds every published epoch", async () => {
  const { browser, page } = await open();
  try {
    await page.locator("summary", { hasText: "Kurvendaten als Tabelle" }).click();
    const rows = page.locator('.training-curve-data tbody tr');
    assert.strictEqual(await rows.count(), 10,
      "the sample run publishes ten epochs; the table must show all of them");
    assert.strictEqual(await page.locator(".training-table-excerpt").count(), 0,
      "a ten-row table was presented as an excerpt");
  } finally {
    await browser.close();
  }
});
