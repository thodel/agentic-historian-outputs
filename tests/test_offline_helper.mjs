// The browser tests' offline rule (tests/support/offline.mjs): what leaves this
// machine is cut, what the tests serve or read themselves is not.
import test from "node:test";
import assert from "node:assert/strict";
import { isExternal } from "./support/offline.mjs";

test("a source image on another host is external", () => {
  assert.equal(isExternal(new URL("https://www.e-codices.unifr.ch/en/saa/0428")), true);
  assert.equal(isExternal(new URL("http://thodel.github.io/agentic-historian-outputs/")), true);
});

test("the fixture servers and files are not", () => {
  for (const url of ["http://127.0.0.1:46393/fixture-mit-quelle/", "http://localhost:8000/",
                     "http://[::1]:8000/", "file:///tmp/fixtures/index.html",
                     "data:image/png;base64,AAAA"]) {
    assert.equal(isExternal(new URL(url)), false, url);
  }
});
