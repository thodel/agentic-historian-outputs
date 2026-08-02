"""Durable editorial review records applied on top of generated pipelines."""
from __future__ import annotations
import json
from copy import deepcopy
from datetime import date
from pathlib import Path

REVIEW_FILE = Path("data/editorial-reviews.json")
STATUSES = {"in-review", "human-verified"}

def load_reviews(path: Path = REVIEW_FILE) -> dict[str, dict]:
    if not path.exists(): return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("version") != 1 or not isinstance(payload.get("documents"), dict):
        raise ValueError("editorial-reviews.json must use version 1 and a documents object")
    reviews = payload["documents"]
    for doc_id, review in reviews.items():
        if not isinstance(review, dict) or review.get("status") not in STATUSES:
            raise ValueError(f"invalid editorial review for {doc_id!r}: unknown status")
        if not str(review.get("reviewer", "")).strip():
            raise ValueError(f"invalid editorial review for {doc_id!r}: reviewer is required")
        try: date.fromisoformat(str(review.get("reviewed_at", "")))
        except ValueError as exc:
            raise ValueError(f"invalid editorial review for {doc_id!r}: reviewed_at must be YYYY-MM-DD") from exc
        if review.get("correction") is not None and not isinstance(review["correction"], dict):
            raise ValueError(f"invalid editorial review for {doc_id!r}: correction must be an object")
    return reviews

def apply_review(data: dict, doc_id: str, reviews: dict[str, dict] | None = None) -> tuple[dict, dict | None]:
    review = (reviews if reviews is not None else load_reviews()).get(doc_id)
    if not review: return data, None
    enriched = deepcopy(data)
    enriched["review_status"] = review["status"]
    correction = review.get("correction") or {}
    if "transcription" in correction: enriched["transcription"] = str(correction["transcription"])
    return enriched, review
