/**
 * tests/integration/styled_site.mjs
 *
 * Everything else in this repository tests generated markup. This tests the
 * site a reader actually gets: built by Jekyll with the real theme, served
 * over HTTP, opened at real viewport sizes.
 *
 * That distinction is not academic. The behavioural fixtures load raw
 * generated HTML from file://, so they cannot see anything the theme does —
 * and the theme was rendering /training/ as an eighty-byte fragment with no
 * head, no navigation and no stylesheet, on a page that is in the public
 * navigation. No amount of asserting on strings in index.md would have found
 * that.
 *
 * Two sites are served, because the suite asks two different kinds of
 * question. The real one (_styled-site) answers "is the site we publish
 * correct" — navigation, language, the empty catalogue, the research index.
 * A fixture one (_styled-fixture) carries two synthetic documents and answers
 * "is a document card correct".
 *
 * They were one site until #254, when every output was withdrawn and five
 * card-level tests failed at once. The site was fine; the suite had been
 * borrowing whatever happened to be published. Skipping them was not an
 * option — see the note above — so they got a corpus of their own.
 *
 * Run:
 *   ./scripts/build_styled_site.sh
 *   ./scripts/build_styled_fixture.sh
 *   node --test tests/integration/styled_site.mjs
 */

import { chromium } from "playwright";
import { createServer } from "node:http";
import { readFile, stat } from "node:fs/promises";
import { existsSync } from "node:fs";
import { extname, join, resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import test, { before, after } from "node:test";
import assert from "node:assert";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..", "..");
const SITE = join(ROOT, "_styled-site");
const FIXTURE = join(ROOT, "_styled-fixture");

const TYPES = {
  ".html": "text/html; charset=utf-8", ".css": "text/css",
  ".js": "text/javascript", ".json": "application/json",
  ".xml": "application/xml", ".svg": "image/svg+xml",
  ".png": "image/png", ".jpg": "image/jpeg", ".zip": "application/zip",
  ".txt": "text/plain; charset=utf-8", ".cff": "text/plain; charset=utf-8",
};

let server;
let fixtureServer;
let browser;
let origin;          // the site we publish
let fixtureOrigin;   // the same site with two synthetic documents in it

before(async () => {
  for (const [path, script] of [[SITE, "build_styled_site.sh"],
                               [FIXTURE, "build_styled_fixture.sh"]]) {
    assert.ok(
      existsSync(path),
      `no built site at ${path}. Run ./scripts/${script} first — ` +
      "this suite deliberately fails rather than skipping, because a test " +
      "that quietly does not run is worse than one that fails.",
    );
  }

  const serve = (root) => createServer(async (request, response) => {
    let path = decodeURIComponent(new URL(request.url, "http://x").pathname);
    let file = join(root, path);
    try {
      if ((await stat(file)).isDirectory()) file = join(file, "index.html");
    } catch {
      response.writeHead(404).end("not found");
      return;
    }
    try {
      const body = await readFile(file);
      response.writeHead(200, {
        "content-type": TYPES[extname(file)] || "application/octet-stream",
      }).end(body);
    } catch {
      response.writeHead(404).end("not found");
    }
  });

  server = serve(SITE);
  fixtureServer = serve(FIXTURE);
  await new Promise(resolve => server.listen(0, "127.0.0.1", resolve));
  await new Promise(resolve => fixtureServer.listen(0, "127.0.0.1", resolve));
  origin = `http://127.0.0.1:${server.address().port}`;
  fixtureOrigin = `http://127.0.0.1:${fixtureServer.address().port}`;
  browser = await chromium.launch({
    headless: true,
    executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH || undefined,
  });
});

after(async () => {
  if (browser) await browser.close();
  if (server) await new Promise(resolve => server.close(resolve));
  if (fixtureServer) await new Promise(resolve => fixtureServer.close(resolve));
});

//: A slow runner needs room: on GitHub Actions a single navigation to this
//: local static site took 11-20 seconds, where it takes under a second here.
const NAVIGATION_TIMEOUT = 60_000;

async function open(path, { width = 1280, height = 720,
                            javaScriptEnabled = true, from = null } = {}) {
  const base = from || origin;
  const context = await browser.newContext({
    viewport: { width, height }, javaScriptEnabled,
  });
  const page = await context.newPage();
  // "load", not "networkidle". This is a static site, so there is no network
  // to go idle — networkidle only adds its 500ms quiet window on top of a
  // page that has already finished, and the browser's own favicon request
  // 404s on every page, which is exactly the kind of straggler it waits on.
  // Measured here: 181ms against 856ms. On the CI runner that multiple ran
  // one test past the 30-second default and failed a correct page. Every
  // assertion below waits on a locator or reads layout after load, so none
  // of them needs the network quiet.
  const response = await page.goto(base + path, {
    waitUntil: "load", timeout: NAVIGATION_TIMEOUT,
  });
  return { page, context, response, origin: base };
}

// ── every page the theme touches must actually be a page ────────────────

test("pages in the public navigation are rendered with the theme", async () => {
  for (const path of ["/", "/training/", "/entities/", "/forschung.html",
                      "/methodology.html", "/about.html"]) {
    const { page, context, response } = await open(path);
    try {
      assert.strictEqual(response.status(), 200, `${path} returned ${response.status()}`);
      assert.strictEqual(
        await page.locator("html").count(), 1,
        `${path} rendered without a layout — no <html>, so no head, no ` +
        "navigation and no stylesheet",
      );
      assert.ok(
        await page.locator("header.site-header, .site-header, nav").first().count() > 0,
        `${path} has no site navigation`,
      );
      const styled = await page.locator("body").evaluate(
        node => getComputedStyle(node).fontFamily);
      assert.ok(styled && styled.length > 0, `${path} has no computed styling`);
    } finally {
      await context.close();
    }
  }
});

test("the site declares the language it is written in", async () => {
  const { page, context } = await open("/");
  try {
    assert.strictEqual(
      await page.locator("html").getAttribute("lang"), "de",
      "the site is German; declaring English misleads screen readers, " +
      "translation and search engines",
    );
  } finally {
    await context.close();
  }
});

// ── the catalogue has to show documents ─────────────────────────────────

for (const [label, width, height] of [["desktop", 1280, 720], ["phone", 390, 844]]) {
  test(`a document is visible without scrolling on ${label}`, async () => {
    const { page, context } = await open("/", { width, height, from: fixtureOrigin });
    try {
      const box = await page.locator(".catalogue-card").first().boundingBox();
      assert.ok(box, "no document card on the catalogue");
      assert.ok(
        box.y < height,
        `the first document card starts at y=${Math.round(box.y)} in a ` +
        `${width}x${height} viewport, so a reader arriving at the catalogue ` +
        "sees no documents at all before scrolling",
      );
    } finally {
      await context.close();
    }
  });
}

test("search and sort are in the open; the rest are behind one disclosure", async () => {
  const { page, context } = await open("/");
  try {
    for (const id of ["catalogue-search", "catalogue-sort"]) {
      assert.ok(await page.locator(`#${id}`).isVisible(), `#${id} is not visible`);
    }
    const advanced = page.locator("details.catalogue-advanced");
    assert.strictEqual(await advanced.count(), 1);
    assert.ok(
      !(await page.locator("#catalogue-language").isVisible()),
      "a secondary filter is open by default, which is what filled the first screen",
    );
    await advanced.locator("summary").click();
    assert.ok(await page.locator("#catalogue-language").isVisible(),
      "the disclosure does not reveal the filters it hides");
  } finally {
    await context.close();
  }
});

test("a missing source is a label, a real facsimile is a thumbnail", async () => {
  const { page, context } = await open("/", { from: fixtureOrigin });
  try {
    const missing = page.locator(".catalogue-source-visual--missing").first();
    const image = page.locator(".catalogue-source-visual--image").first();
    assert.ok(await missing.count() > 0, "no missing-source card to check");
    assert.ok(await image.count() > 0, "no facsimile card to check");

    const missingBox = await missing.boundingBox();
    const imageBox = await image.boundingBox();
    assert.ok(
      missingBox.height < imageBox.height / 2,
      `the placeholder for an absent source is ${Math.round(missingBox.height)}px ` +
      `against ${Math.round(imageBox.height)}px for a real facsimile; an absence ` +
      "should not take the space of evidence",
    );
  } finally {
    await context.close();
  }
});

// ── the site has to work without JavaScript ─────────────────────────────

test("the catalogue and its documents are navigable without JavaScript", async () => {
  const { page, context } = await open("/", { javaScriptEnabled: false, from: fixtureOrigin });
  try {
    const cards = await page.locator(".catalogue-card").count();
    assert.ok(cards > 0, "no documents are listed without JavaScript");

    const link = page.locator('.catalogue-card a[href$="/"]').first();
    const href = await link.getAttribute("href");
    await link.click();
    await page.waitForLoadState("domcontentloaded");
    assert.ok(
      page.url().includes(href.replace(/^\.?\//, "")),
      `following ${href} without JavaScript did not reach the document`,
    );
    assert.ok(await page.locator("h1").count() > 0, "the document page is empty");
  } finally {
    await context.close();
  }
});

test("the citable downloads a document offers all resolve", async () => {
  // A fixture document, not a published one: /u-17/ was used here only
  // because it was the one document with mapped pages, and it is withdrawn.
  const { page, context } = await open("/fixture-mit-quelle/", { from: fixtureOrigin });
  try {
    const hrefs = await page.locator('#downloads a[href]').evaluateAll(
      nodes => nodes.map(node => node.getAttribute("href")));
    assert.ok(hrefs.length > 0, "the document offers no downloads");
    for (const href of hrefs) {
      if (/^https?:/.test(href)) continue;   // external rights statements
      const target = new URL(href, `${fixtureOrigin}/fixture-mit-quelle/`).toString();
      const response = await page.request.get(target);
      assert.strictEqual(
        response.status(), 200,
        `${href} on /fixture-mit-quelle/ resolves to ${response.status()} — a citable ` +
        "artifact that 404s is worse than one that is not offered",
      );
    }
  } finally {
    await context.close();
  }
});

test("the empty training section explains itself", async () => {
  const { page, context } = await open("/training/");
  try {
    const text = await page.locator("body").innerText();
    assert.match(text, /Trainingsläufe/,
      "the training page does not say what it is waiting for");
    const headings = await page.locator("h1").allInnerTexts();
    assert.strictEqual(
      headings.length, 1,
      `the training page renders ${headings.length} top-level headings: ` +
      JSON.stringify(headings),
    );
  } finally {
    await context.close();
  }
});

// ── the research section ────────────────────────────────────────────────

test("the research index reaches both studies, and says they are English", async () => {
  const { page, context } = await open("/forschung.html");
  try {
    for (const target of ["evaluation.html", "vlm-finetuning.html"]) {
      const link = page.locator(`a[href="${target}"]`).first();
      assert.strictEqual(await link.count(), 1, `${target} is not linked`);

      const response = await page.request.get(new URL(target, origin + "/").toString());
      assert.strictEqual(
        response.status(), 200,
        `${target} is linked from the navigation but resolves to ` +
        `${response.status()}`,
      );
    }
    const text = await page.locator("body").innerText();
    const marks = text.match(/englisch/gi) || [];
    assert.ok(
      marks.length >= 2,
      "the research index links English pages without marking them as English",
    );
  } finally {
    await context.close();
  }
});

test("a research page no longer calls itself an internal document", async () => {
  for (const path of ["/evaluation.html", "/vlm-finetuning.html"]) {
    const { page, context } = await open(path);
    try {
      const text = await page.locator("body").innerText();
      assert.ok(
        !text.includes("Internal engineering document"),
        `${path} is in the public navigation but still presents itself as an ` +
        "internal working document",
      );
      assert.match(text, /in English/,
        `${path} does not tell a reader it is in English`);
    } finally {
      await context.close();
    }
  }
});

// ── what the site looks like with nothing published ─────────────────────

test("an empty catalogue explains itself instead of showing bare filters", async () => {
  const { page, context } = await open("/");
  try {
    const cards = await page.locator(".catalogue-card").count();
    const notice = page.locator(".catalogue-no-outputs");
    if (cards > 0) {
      assert.strictEqual(await notice.count(), 0,
        "the catalogue lists outputs and also claims to have none");
      return;
    }
    assert.strictEqual(
      await notice.count(), 1,
      "the catalogue has no documents and does not say why; a page of " +
      "filters over nothing reads as broken rather than empty",
    );
    const text = await notice.innerText();
    assert.match(text, /zurückgezogen/,
      "the notice does not say the outputs were withdrawn");
    assert.ok(
      await notice.boundingBox(),
      "the explanation is in the markup but not visible to a reader",
    );
  } finally {
    await context.close();
  }
});

test("a withdrawn document keeps its URL and says it must not be cited", async () => {
  const { page, context, response } = await open("/u-17/");
  try {
    assert.strictEqual(
      response.status(), 200,
      "withdrawal is not deletion: the URL has to go on resolving, or every " +
      "citation of it breaks silently",
    );
    const text = await page.locator("body").innerText();
    assert.match(text, /must not be cited/);
    assert.ok(
      await page.locator("header.site-header, .site-header, nav").first().count() > 0,
      "the tombstone renders without the theme",
    );
    const robots = await page.locator('meta[name="robots"]').getAttribute("content");
    assert.match(String(robots), /noindex/,
      "a withdrawn output is still being offered to search engines");
  } finally {
    await context.close();
  }
});
