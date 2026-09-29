#!/usr/bin/env python3
"""How big is the generated site, and what is making it big (#239).

The repository had per-run and per-page budgets but no figure for the site as
a whole, so nothing would notice a corpus import until GitHub Pages did. The
numbers that matter are not the totals, though — they are the *per document*
costs, because those are what a corpus multiplies.

At the time this was written a single document page was 325 KB of generated
markup. Eight of those is unremarkable; two thousand is 650 MB, against a
Pages limit of 1 GB and a ten-minute build. The projection below exists to
make that visible while the corpus is still small enough to change course.

This reports and exits non-zero when over budget. It deliberately does not
raise during generation: a budget that aborts the build cannot be acted on,
it can only block publishing — the same cliff that made a long training run a
publication blocker (#227).
"""

from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path

# GitHub Pages refuses a published site over 1 GB. Half of that is the point
# at which the shape of the site has to change rather than the point at which
# it breaks.
SITE_BUDGETS = {
    "total_bytes": 500_000_000,
    # One document's generated page. The recognition viewer embeds every
    # candidate's text, so this grows with the number of recognition attempts,
    # not with the length of the document.
    "document_page_bytes": 400_000,
    # What the projection is reported against — the scale #239 asks about.
    "projection_documents": 2000,
}

#: Written by Jekyll and by local tooling, never published.
EXCLUDED_DIRECTORIES = {".jekyll-cache", "_site", ".sass-cache"}


def _iter_files(docs_root: Path):
    for path in sorted(docs_root.rglob("*")):
        if not path.is_file():
            continue
        parts = path.relative_to(docs_root).parts
        if any(part in EXCLUDED_DIRECTORIES for part in parts):
            continue
        yield path


def _area(relative: Path, document_ids: set[str]) -> str:
    parts = relative.parts
    if len(parts) == 1:
        return "(root)"
    head = parts[0]
    if head in {"entities", "assets", "training", "tests"}:
        return f"{head}/"
    if head in document_ids:
        return "documents/"
    # Tombstones and standalone pages: one directory each, and listing them
    # individually buries the numbers that matter under a dozen 947-byte rows.
    return "other pages/"


def measure(docs_root: Path) -> dict:
    """Total, per-area and per-document sizes, plus the largest files."""
    document_ids = {
        path.parent.name for path in docs_root.glob("*/pipeline.json")
    }
    areas: dict[str, int] = defaultdict(int)
    counts: dict[str, int] = defaultdict(int)
    per_document: dict[str, int] = defaultdict(int)
    largest: list[tuple[int, str]] = []
    total = 0

    for path in _iter_files(docs_root):
        size = path.stat().st_size
        relative = path.relative_to(docs_root)
        total += size
        area = _area(relative, document_ids)
        areas[area] += size
        counts[area] += 1
        if relative.parts[0] in document_ids:
            per_document[relative.parts[0]] += size
        largest.append((size, str(relative)))

    largest.sort(reverse=True)
    page_sizes = {
        doc_id: (docs_root / doc_id / "index.md").stat().st_size
        for doc_id in sorted(document_ids)
        if (docs_root / doc_id / "index.md").exists()
    }
    mean_page = sum(page_sizes.values()) // len(page_sizes) if page_sizes else 0
    mean_document = (
        sum(per_document.values()) // len(per_document) if per_document else 0
    )
    return {
        "total_bytes": total,
        "documents": len(document_ids),
        "areas": dict(areas),
        "area_counts": dict(counts),
        "per_document": dict(per_document),
        "page_sizes": page_sizes,
        "mean_page_bytes": mean_page,
        "mean_document_bytes": mean_document,
        "largest_files": largest[:10],
    }


def violations(report: dict) -> list[str]:
    """Budget breaches, worst first. Empty means within budget."""
    problems = []
    if report["total_bytes"] > SITE_BUDGETS["total_bytes"]:
        problems.append(
            f'generated site is {report["total_bytes"]:,} bytes, over the '
            f'{SITE_BUDGETS["total_bytes"]:,} budget'
        )
    over = sorted(
        ((size, doc_id) for doc_id, size in report["page_sizes"].items()
         if size > SITE_BUDGETS["document_page_bytes"]),
        reverse=True,
    )
    for size, doc_id in over:
        problems.append(
            f'document page {doc_id} is {size:,} bytes, over the '
            f'{SITE_BUDGETS["document_page_bytes"]:,} per-page budget'
        )
    return problems


def projection(report: dict, documents: int | None = None) -> str:
    """What the current per-document cost implies at corpus scale."""
    documents = documents or SITE_BUDGETS["projection_documents"]
    if not report["mean_document_bytes"]:
        return "No documents published; nothing to project."
    projected = report["mean_document_bytes"] * documents
    fixed = report["total_bytes"] - sum(report["per_document"].values())
    total = projected + fixed
    verdict = "within" if total <= SITE_BUDGETS["total_bytes"] else "OVER"
    return (
        f'At {report["mean_document_bytes"]:,} bytes per document '
        f'({report["mean_page_bytes"]:,} of it the generated page), '
        f'{documents:,} documents would render at least {total:,} bytes — '
        f'{verdict} the {SITE_BUDGETS["total_bytes"]:,} budget.\n'
        "This is a floor, not an estimate: it scales the documents and holds "
        "everything else fixed, while entity pages grow with the corpus too."
    )


def report_text(report: dict) -> str:
    lines = [
        f'Generated site: {report["total_bytes"]:,} bytes across '
        f'{report["documents"]} document(s)',
        "",
        f'{"area":16}{"files":>7}{"bytes":>14}',
        "-" * 37,
    ]
    for area, size in sorted(report["areas"].items(), key=lambda item: -item[1]):
        lines.append(f'{area:16}{report["area_counts"][area]:>7}{size:>14,}')
    lines += ["", "Largest single files:"]
    for size, name in report["largest_files"][:5]:
        lines.append(f"  {size:>12,}  {name}")
    lines += ["", projection(report)]
    problems = violations(report)
    if problems:
        lines += ["", "Over budget:"] + [f"  - {problem}" for problem in problems]
    return "\n".join(lines)


def main() -> int:
    from build_outputs import DOCS

    report = measure(DOCS)
    print(report_text(report))
    return 1 if violations(report) else 0


if __name__ == "__main__":
    raise SystemExit(main())
