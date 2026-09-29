---
layout: page
title: Withdrawal policy
permalink: /withdrawal-policy/
---

# Withdrawal policy

Document identifiers in this repository become permanent public URLs. Publication
therefore cannot be undone by deleting a directory or silently sending its URL
somewhere else. When an output should no longer be presented as a research output,
the repository preserves its URL as a **tombstone** and records why it was withdrawn.

## When withdrawal is appropriate

Withdrawal is exceptional. It is appropriate when the published object:

- is an engineering fixture or test run that was never intended as a research
  output;
- identifies the wrong source or contains a fundamental attribution error that
  cannot be handled as an ordinary correction;
- exposes material that cannot remain public for legal, rights, privacy, or ethical
  reasons; or
- is so corrupt or misleading that continuing to distribute it as an output would
  cause harm.

A newer or improved processing run is **not** grounds for withdrawal. It must use the
`supersedes` relation so both versions remain citable and their lineage stays visible.
A duplicate or malformed id should likewise be related to the canonical record with
`supersedes` whenever it represents a genuine published run. Ordinary transcription,
metadata, and entity errors should be corrected through the editorial workflow rather
than withdrawn.

## What happens to a withdrawn id

The existing `docs/<id>/` URL remains resolvable and displays a tombstone. The
tombstone must:

- state plainly that the output has been withdrawn and must not be cited as a current
  research output;
- give the withdrawal date and a public reason;
- identify the accountable decision through a repository issue or other stable public
  reference; and
- link to a replacement or canonical output when one exists.

The withdrawn record is excluded from the public catalogue, catalogue totals, search
and filters, the Atom feed, sitemap, entity indexes, and generated statistics. Its
transcription, recognition package, entities, and citation metadata are no longer
offered from the live tombstone. The repository's Git history remains the audit trail
for what was previously published and when.

Direct deletion is reserved for material that must be removed from Git history for a
legal, security, privacy, or comparable safety reason. That exceptional operation
requires a separate documented decision; it is not the normal withdrawal process.

## Obsolete entity pages

Entity pages under `docs/entities/<slug>/` are generated from the entities named in
current records, and their URLs are citable in the same way document URLs are. When a
document is re-recognised, superseded, or corrected, entities it used to mention stop
being generated — but the page remains. Such a page is **obsolete**, not withdrawn:
no decision was taken about it, the evidence behind it simply moved.

Obsolescence and withdrawal therefore have different outcomes:

- an **obsolete** entity page keeps its URL and becomes a tombstone, because deleting
  it would break citations nobody decided to invalidate;
- an entity page whose only evidence came from a **withdrawn** output is deleted,
  because the withdrawal decision says that material must stop being presented.

The generators enforce this by reconciling against the manifest of entity pages the
build actually produced, and by running withdrawal removal before tombstoning. An
obsolete-entity tombstone must:

- state plainly that no current output supports the entity;
- keep the label the URL was cited under;
- carry no evidence table and no links presented as sources; and
- be marked `noindex` and excluded from the sitemap.

Tombstoning is idempotent — a tombstone re-derives its label from itself, so rebuilds
produce identical bytes — and reversible: an entity that reappears in a record is
regenerated as an ordinary page, because generation runs before reconciliation. The
last published version of the page, including its evidence table, remains in Git
history.

## Required withdrawal record

Withdrawal state must live in committed source data, not in a hand-edited generated
page. The implementation must preserve at least these fields:

- permanent document id;
- status (`withdrawn`);
- withdrawal date in ISO 8601 format;
- short public reason;
- stable decision reference;
- replacement document id or URL, when applicable.

Generators are responsible for producing the tombstone and enforcing exclusion from
every discovery surface. This keeps regeneration reproducible and prevents a
withdrawn record from returning to the catalogue accidentally.

## Applying this policy

Each withdrawal requires its own reviewable commit or pull request and a linked issue
that records the grounds and verifies the resulting tombstone and discovery removal.
Restoring a withdrawn id requires the same documented process; the original withdrawal
record remains in Git history.

The `saa-0001-test` through `saa-0006-test` records meet the first ground above. They
should be converted to tombstones under this policy, not deleted or redirected. Their
removal and the build-time prevention of future test-id publication are tracked
separately so this policy decision remains auditable and implementation-independent.
