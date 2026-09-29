#!/usr/bin/env bash
# Build the site the way GitHub Pages does, for tests/integration/styled_site.mjs.
#
# The behavioural fixtures load raw generated HTML from file://, so nothing in
# the suite could see what the Jekyll theme does to a page. That is how
# /training/ came to be served as an eighty-byte fragment with no head, no
# navigation and no stylesheet, on a page that is in the public navigation.
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
out="$root/_styled-site"

export PATH="$PATH:$(ruby -e 'print Gem.bindir' 2>/dev/null || echo '')"
if ! command -v jekyll >/dev/null 2>&1; then
  echo "jekyll not found. Install it with: gem install --no-document jekyll minima" >&2
  exit 1
fi

rm -rf "$out"
jekyll build -s "$root/docs" -d "$out" --quiet
echo "Built styled site at $out"
