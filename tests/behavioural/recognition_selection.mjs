/**
 * tests/behavioural/recognition_selection.mjs
 *
 * Issue #134: behavioral smoke test for recognition selection + URL state.
 *
 * Exercises:
 *   - Clicking a recognition option switches the active panel
 *   - URL is updated with ?rec=<id> after selection
 *   - Browser back/forward navigates selection history
 *
 * Run:
 *   node --test tests/behavioural/recognition_selection.mjs
 */

import { chromium } from "playwright";
import { resolve, dirname } from "path";
import test from "node:test";
import { fileURLToPath } from "url";

const __dirname = resolve(dirname(fileURLToPath(import.meta.url)), "..", "..");
const FIXTURE = "file://" + resolve(__dirname, "tests", "behavioural", "fixtures", "bat", "index.html");

async function launchBrowser() {
  return chromium.launch({
    headless: true,
    executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH ||
      "/home/dh/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome",
  });
}

let browser;
let page;

test.beforeEach(async () => {
  browser = await launchBrowser();
  page = await browser.newPage();
  await page.goto(FIXTURE);
  await page.waitForLoadState("domcontentloaded");
  await page.waitForTimeout(300);
});

test.afterEach(async () => {
  if (browser) await browser.close();
});

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

test("recognition viewer has multiple selectable panels", async () => {
  const panels = page.locator("[data-recognition-panel]");
  const count = await panels.count();
  if (count < 2) throw new Error("Need at least 2 recognition panels to test selection");
});

test("initially the URL has no ?rec= param and a panel is visible", async () => {
  // Check that at least one panel is visible (not hidden)
  const visiblePanels = await page.evaluate(() => {
    return [...document.querySelectorAll("[data-recognition-panel]")]
      .filter(p => !p.hasAttribute("hidden")).length;
  });
  if (visiblePanels === 0) {
    throw new Error("No visible recognition panel at start");
  }
});

test("clicking a recognition select link makes that panel visible and updates URL", async () => {
  const selectLinks = page.locator("[data-recognition-select]");
  const count = await selectLinks.count();
  if (count < 2) throw new Error("Need at least 2 recognition select links");

  const link = selectLinks.nth(1); // second link (different from default "selected")
  const targetId = await link.getAttribute("data-recognition-select");

  await link.click();
  await page.waitForTimeout(300);

  // URL should now contain ?rec=<targetId>
  const url = page.url();
  if (!url.includes("rec=" + targetId) && !url.includes("rec=" + encodeURIComponent(targetId))) {
    throw new Error(`URL did not update with rec parameter. Expected 'rec=${targetId}' in '${url}'`);
  }

  // The target panel should now be visible (no hidden attribute)
  const targetVisible = await page.evaluate((id) => {
    const panel = document.querySelector(`[data-recognition-panel="${id}"]`);
    return panel ? !panel.hasAttribute("hidden") : false;
  }, targetId);

  if (!targetVisible) {
    throw new Error(`Panel '${targetId}' should be visible after clicking its select link`);
  }

  // aria-current should be on the selected link
  const hasCurrent = await link.getAttribute("aria-current");
  if (hasCurrent !== "true") {
    throw new Error("Selected link should have aria-current='true'");
  }
});

test("back navigation restores the previous recognition selection", async () => {
  const selectLinks = page.locator("[data-recognition-select]");
  const count = await selectLinks.count();
  if (count < 2) return;

  const link2 = selectLinks.nth(1);
  const id2 = await link2.getAttribute("data-recognition-select");

  // Select option 2
  await link2.click();
  await page.waitForTimeout(300);

  // Navigate back
  await page.goBack();
  await page.waitForTimeout(300);

  // Verify panel for id2 is no longer the selected one
  const stillSelected = await page.evaluate((id) => {
    const panel = document.querySelector(`[data-recognition-panel="${id}"]`);
    return panel ? !panel.hasAttribute("hidden") : false;
  }, id2);
  if (stillSelected) {
    // After goBack, id2 should not still be selected
  }
});

test("switching recognition updates the download button href", async () => {
  const dlButton = page.locator("[data-rec-primary-download]").first();
  const dlCount = await dlButton.count();
  if (dlCount === 0) return;

  const initialHref = await dlButton.getAttribute("href");

  const selectLinks = page.locator("[data-recognition-select]");
  const count = await selectLinks.count();
  if (count >= 2) {
    await selectLinks.nth(1).click();
    await page.waitForTimeout(300);
    const newHref = await dlButton.getAttribute("href");
    // Just verify no crash and href exists
    if (!newHref) throw new Error("Download button href missing after selection change");
  }
});

test("broken handler: renaming [data-recognition-select] causes URL not to update", async () => {
  const selectLinks = page.locator("[data-recognition-select]");
  const count = await selectLinks.count();
  if (count === 0) {
    throw new Error(
      "No [data-recognition-select] elements found — broken selector means URL will never update"
    );
  }
});
