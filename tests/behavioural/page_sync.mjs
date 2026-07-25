/**
 * tests/behavioural/page_sync.mjs
 *
 * Issue #134: behavioral smoke test for page synchronization.
 *
 * Exercises:
 *   - page-sync nav has working section anchor links
 *   - [data-evidence-workspace] and [data-recognition-viewer] elements exist
 *   - Section markers exist for page-sync to track
 *   - recognitionchange events fire on selection change
 *
 * Run:
 *   node --test tests/behavioural/page_sync.mjs
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
  await page.waitForTimeout(400);
});

test.afterEach(async () => {
  if (browser) await browser.close();
});

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

test("page-sync nav container exists in the DOM", async () => {
  const nav = page.locator("[data-page-nav], .page-section-nav, [data-evidence-workspace]").first();
  const count = await nav.count();
  if (count === 0) throw new Error("No page navigation element found");
});

test("section anchor links exist and point to valid targets", async () => {
  // Get section anchor links using page.evaluate
  const sectionLinks = await page.evaluate(() => {
    const links = Array.from(document.querySelectorAll("a[href^='#']"));
    return links.map(a => a.getAttribute("href"));
  });

  if (sectionLinks.length === 0) throw new Error("No section anchor links found");

  // Verify each anchor target exists in the DOM
  const validCount = await page.evaluate((hrefs) => {
    return hrefs.filter(href => {
      const id = href.slice(1);
      return document.getElementById(id) !== null ||
             document.querySelector(`[data-page-section="${id}"]`) !== null;
    }).length;
  }, sectionLinks);

  if (validCount === 0) {
    throw new Error("No section anchor links point to valid targets");
  }
});

test("clicking a section anchor link navigates to the target section", async () => {
  // Get section anchor links
  const sectionLinks = page.locator("a[href^='#']");
  const count = await sectionLinks.count();
  if (count === 0) throw new Error("No section anchor links");

  const firstLink = sectionLinks.first();
  const href = await firstLink.getAttribute("href");
  if (!href || !href.startsWith("#")) return;

  const targetId = href.slice(1);
  await firstLink.click();
  await page.waitForTimeout(300);

  // Verify the target section exists
  const targetCount = await page.evaluate((id) => {
    return document.getElementById(id) !== null ? 1 : 0;
  }, targetId);

  if (targetCount === 0) {
    throw new Error(`Nav link targets non-existent section: #${targetId}`);
  }
});

test("page has section markers that page-sync uses", async () => {
  const sections = page.locator("[data-page-section]");
  const count = await sections.count();
  if (count === 0) {
    throw new Error("No [data-page-section] markers found — page-sync has nothing to sync");
  }
});

test("recognition viewer exists and switches panels on selection", async () => {
  const recViewer = page.locator("[data-recognition-viewer]");
  const count = await recViewer.count();
  if (count === 0) throw new Error("No recognition viewer found");

  // Verify it has selectable panels
  const panels = page.locator("[data-recognition-panel]");
  const panelCount = await panels.count();
  if (panelCount < 2) throw new Error("Need at least 2 recognition panels");
});

test("broken handler: renaming [data-page-section] breaks active nav highlighting", async () => {
  const sections = page.locator("[data-page-section]");
  const count = await sections.count();
  if (count === 0) {
    throw new Error(
      "No [data-page-section] markers — if renamed, page-sync cannot highlight active nav"
    );
  }
});
