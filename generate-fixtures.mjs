/**
 * generate-fixtures.mjs
 *
 * Converts markdown source files in docs/ into standalone HTML fixtures
 * that can be loaded via file:// URLs in Playwright tests.
 *
 * JS assets are inlined as <script> tags so they work without a server.
 * CSS assets are copied to the fixtures directory for relative resolution.
 *
 * Usage:
 *   node generate-fixtures.mjs
 *   node --test tests/behavioural/*.mjs
 */

import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));

// Where the pages come from, and which of them become fixtures.
//
// These were `docs/` and a hardcoded ["bat", "u-17"]. Both documents were
// withdrawn (#254), so their pages became tombstones and 24 of the 40
// behavioural cases had nothing to find — the suite had been built on two
// specific published outputs rather than on a corpus of its own. The defaults
// below keep the old behaviour for a local run against the real site; CI
// points them at a synthetic corpus built by tests/fixtures/styled_fixture.py.
const DOCS      = process.env.AH_FIXTURE_DOCS
  ? join(process.cwd(), process.env.AH_FIXTURE_DOCS)
  : join(__dirname, "docs");
const DOC_IDS   = (process.env.AH_FIXTURE_DOC_IDS || "bat,u-17")
  .split(",").map(id => id.trim()).filter(Boolean);
const FIXTURES  = join(__dirname, "tests", "behavioural", "fixtures");
const ASSETS    = join(DOCS, "assets");
const ASSETS_REL = "assets";

// ---------------------------------------------------------------------------
// Generated pages are YAML frontmatter followed by HTML. Preserve that HTML
// directly so the behavioral suite has no undeclared Python/Jekyll dependency.
// ---------------------------------------------------------------------------

function mdToHtml(source) {
  const content = source
    .replace(/^---\n[\s\S]*?\n---\n/, "")
    .replace(/\{\{\{?\s*'\/assets\/([^']+)'\s*\|\s*relative_url\s*\}\}\}?/g, "/assets/$1");
  return `<!DOCTYPE html>
<html lang="de">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Test Fixture</title></head>
<body>${content}</body>
</html>`;
}

// ---------------------------------------------------------------------------
// Per-page inline scripts
// ---------------------------------------------------------------------------

const PAGE_SCRIPTS = {
  "document": [
    "quality-explain.js",
    "rec-viewer.js",
    "page-sync.js",
    "page-disclosure.js",
    "workspace.js",
    "evidence-viewer.js",
  ],
  "catalogue": [
    "catalogue.js",
    "quality-explain.js",
  ],
  "index": [
    "catalogue.js",
  ],
};

function inlineScripts(pageType) {
  const names = PAGE_SCRIPTS[pageType] || PAGE_SCRIPTS["document"];
  return names.map(name => {
    const src = join(ASSETS, name);
    if (!existsSync(src)) return "";
    const content = readFileSync(src, "utf8");
    if (name.endsWith(".js")) {
      return `\n<script>\n(function(){\n${content}\n})();\n</script>\n`;
    }
    return "";
  }).join("");
}

// ---------------------------------------------------------------------------
// Page-type detection
// ---------------------------------------------------------------------------

function detectPageType(filePath) {
  if (filePath.includes("/bat/") || filePath.includes("/u-17/") ||
      filePath.includes("/kf-/") || filePath.includes("/könige")) {
    return "document";
  }
  if (filePath.endsWith("/index.md") && dirname(filePath).endsWith("/docs")) {
    return "catalogue";
  }
  return "document";
}

// ---------------------------------------------------------------------------
// Copy CSS/font assets to fixtures directory
// ---------------------------------------------------------------------------

const ALL_ASSETS = [
  "quality-explain.js", "rec-viewer.js", "page-sync.js",
  "page-disclosure.js", "evidence-viewer.js", "workspace.js",
  "catalogue.js", "output.css", "catalogue.css",
];

function setupAssets() {
  const assetsDest = join(FIXTURES, ASSETS_REL);
  mkdirSync(assetsDest, { recursive: true });
  for (const asset of ALL_ASSETS) {
    const src = join(ASSETS, asset);
    if (existsSync(src)) {
      writeFileSync(join(assetsDest, asset), readFileSync(src));
    }
  }
}

// ---------------------------------------------------------------------------
// Generate fixtures
// ---------------------------------------------------------------------------

function generateDocumentFixture(mdPath) {
  const raw = readFileSync(mdPath, "utf8");
  const html = mdToHtml(raw);
  const pageType = detectPageType(mdPath);
  const scripts = inlineScripts(pageType);
  const withAssets = html.replace("</body>", scripts + "</body>");
  const rel = mdPath.replace(DOCS + "/", "").replace(/\.md$/, ".html");
  const outPath = join(FIXTURES, rel);
  mkdirSync(dirname(outPath), { recursive: true });
  writeFileSync(outPath, withAssets, "utf8");
  console.log("Generated: " + outPath);
}

function generateCatalogueFixture(mdPath) {
  const raw = readFileSync(mdPath, "utf8");
  const html = mdToHtml(raw);
  const scripts = inlineScripts("catalogue");
  const withAssets = html.replace("</body>", scripts + "</body>");
  const outPath = join(FIXTURES, "index.html");
  writeFileSync(outPath, withAssets, "utf8");
  console.log("Generated catalogue: " + outPath);
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

function main() {
  if (!existsSync(DOCS)) {
    console.error("docs/ not found at " + DOCS);
    process.exit(1);
  }
  mkdirSync(FIXTURES, { recursive: true });
  setupAssets();

  let written = 0;
  for (const id of DOC_IDS) {
    const p = join(DOCS, id, "index.md");
    if (existsSync(p)) {
      generateDocumentFixture(p);
      written += 1;
    }
  }
  if (written === 0) {
    console.error(
      `No document fixtures written. Looked for ${DOC_IDS.join(", ")} under ` +
      `${DOCS}. The behavioural suite cannot run against nothing, and a ` +
      "fixture that silently does not exist fails every case with \"no " +
      "element found\" rather than saying why.");
    process.exit(1);
  }

  const indexPage = join(DOCS, "index.md");
  if (existsSync(indexPage)) generateCatalogueFixture(indexPage);

  console.log("\nFixtures written to " + FIXTURES);
}

main();
