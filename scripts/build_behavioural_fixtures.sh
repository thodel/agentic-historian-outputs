#!/usr/bin/env bash
# Build the HTML fixtures the behavioural suite loads from file://.
#
# The suite used to convert docs/bat/ and docs/u-17/ into fixtures, so it was
# built on two specific published outputs. Both were withdrawn (#254), their
# pages became tombstones, and 24 of 40 cases failed with "no element found" —
# the site was fine, the suite had no corpus of its own. It has one now.
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
src="$root/_styled-fixture-src"

python3 "$root/tests/fixtures/styled_fixture.py" "$src" >/dev/null
python3 "$root/tests/generate_training_fixture.py"

AH_FIXTURE_DOCS="$(realpath --relative-to="$PWD" "$src/docs")" \
AH_FIXTURE_DOC_IDS="fixture-mit-quelle,fixture-ohne-quelle" \
  node "$root/generate-fixtures.mjs"
