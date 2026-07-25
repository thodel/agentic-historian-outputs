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

import { spawnSync } from "node:child_process";
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const DOCS      = join(__dirname, "docs");
const FIXTURES  = join(__dirname, "tests", "behavioural", "fixtures");
const ASSETS    = join(DOCS, "assets");
const ASSETS_REL = "assets";

// ---------------------------------------------------------------------------
// Markdown → HTML (via external Python script)
// ---------------------------------------------------------------------------

function mdToHtml(markdown) {
  const result = spawnSync("python3", [join(__dirname, "_md_to_html.py")], {
    input: markdown,
    encoding: "utf8",
    maxBuffer: 10 * 1024 * 1024,
  });
  if (result.status !== 0) throw new Error("markdown conversion failed: " + result.stderr);
  return result.stdout;
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
  // build_index.py adds catalogue-superseded after catalogue-failure via Python-side
  // processing; inject it here so initCatalogue does not bail early.
  const supersededControl = `<div>
    <label for="catalogue-superseded">Ersetzte Einträge</label>
    <select id="catalogue-superseded">
      <option value="hide">Verbergen</option>
      <option value="show">Anzeigen</option>
    </select>
  </div>
`;
  const withSuperseded = withAssets.replace(
    '<label for="catalogue-source">',
    supersededControl + '<label for="catalogue-source">'
  );
  const outPath = join(FIXTURES, "index.html");
  writeFileSync(outPath, withSuperseded, "utf8");
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

  for (const p of [
    join(DOCS, "bat", "index.md"),
    join(DOCS, "u-17", "index.md"),
  ]) {
    if (existsSync(p)) generateDocumentFixture(p);
  }

  const indexPage = join(DOCS, "index.md");
  if (existsSync(indexPage)) generateCatalogueFixture(indexPage);

  console.log("\nFixtures written to " + FIXTURES);
}

main();
