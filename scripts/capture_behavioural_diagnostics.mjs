import { mkdir } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const output = resolve(root, "test-results", "browser");
const executablePath = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH;
const fixtures = [
  ["catalogue", resolve(root, "tests", "behavioural", "fixtures", "index.html")],
  ["document", resolve(root, "tests", "behavioural", "fixtures", "bat", "index.html")],
];

await mkdir(output, { recursive: true });
const browser = await chromium.launch({
  headless: true,
  ...(executablePath ? { executablePath } : {}),
});

try {
  for (const [name, fixture] of fixtures) {
    const context = await browser.newContext();
    await context.tracing.start({ screenshots: true, snapshots: true, sources: true });
    const page = await context.newPage();
    await page.goto(`file://${fixture}`);
    await page.waitForLoadState("domcontentloaded");
    await page.screenshot({ path: resolve(output, `${name}.png`), fullPage: true });
    await context.tracing.stop({ path: resolve(output, `${name}-trace.zip`) });
    await context.close();
  }
} finally {
  await browser.close();
}
