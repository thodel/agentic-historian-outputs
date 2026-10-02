#!/usr/bin/env bash
# Build a themed site over a small synthetic corpus, for tests/integration.
#
# The card-level tests in styled_site.mjs need documents. They used to borrow
# whatever was published, so every one of them failed when the corpus was
# withdrawn (#254) — the site was fine, the suite had just been depending on
# the corpus being non-empty. This gives them two documents of their own.
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
src="$root/_styled-fixture-src"
out="$root/_styled-fixture"

export PATH="$PATH:$(ruby -e 'print Gem.bindir' 2>/dev/null || echo '')"
if ! command -v jekyll >/dev/null 2>&1; then
  echo "jekyll not found. Install it with: gem install --no-document jekyll minima" >&2
  exit 1
fi

python3 "$root/tests/fixtures/styled_fixture.py" "$src" >/dev/null
rm -rf "$out"
jekyll build -s "$src/docs" -d "$out" --quiet
echo "Built styled fixture site at $out"
