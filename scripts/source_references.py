"""Normalize publication-safe source references for generated document pages."""

from __future__ import annotations

import ipaddress
from urllib.parse import urlparse


PLACEHOLDER_HOSTS = {"example.com", "example.org", "example.net", "localhost", "test.invalid"}
IMAGE_SUFFIXES = (".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff")


def _text(value: object) -> str:
    if isinstance(value, dict):
        value = value.get("value") or value.get("wert") or ""
    return str(value or "").strip()


def public_url(value: object) -> str:
    """Return a safe HTTP(S) URL, or an empty string for non-public input."""
    url = _text(value)
    if not url or any(char.isspace() for char in url):
        return ""
    parsed = urlparse(url)
    host = (parsed.hostname or "").rstrip(".").casefold()
    if parsed.scheme not in {"http", "https"} or not host or parsed.username or parsed.password:
        return ""
    if host in PLACEHOLDER_HOSTS or host.endswith(".example.com") or host.endswith(".invalid"):
        return ""
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        address = None
    if address and not address.is_global:
        return ""
    return url


def _kind(url: str, explicit_manifest: bool = False) -> str:
    path = urlparse(url).path.casefold()
    if explicit_manifest or "manifest" in path or path.endswith(".json"):
        return "iiif_manifest"
    if path.endswith(IMAGE_SUFFIXES):
        return "image"
    return "landing_page"


def _page_map(data: dict) -> list[dict[str, str]]:
    raw = data.get("source_pages") or data.get("page_mapping") or []
    if isinstance(raw, dict):
        raw = [{"page": page, **(item if isinstance(item, dict) else {"url": item})}
               for page, item in raw.items()]
    if not isinstance(raw, list):
        return []
    result = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        page = _text(item.get("page") or item.get("page_id") or item.get("recognition_page"))
        canvas = public_url(item.get("canvas") or item.get("canvas_url"))
        image = public_url(item.get("image") or item.get("image_url") or item.get("url"))
        if page and (canvas or image):
            result.append({"page": page, "canvas_url": canvas, "image_url": image})
    return result


def normalize_source_reference(data: dict) -> dict:
    """Return the stable, minimal source payload exposed to the frontend."""
    manifest = public_url(data.get("iiif_manifest") or data.get("manifest_url"))
    source = public_url(data.get("source_url"))
    primary = manifest or source
    kind = _kind(primary, explicit_manifest=bool(manifest)) if primary else "missing"
    return {
        "type": kind,
        "label": _text(data.get("source_label") or data.get("label")),
        "attribution": _text(data.get("source_attribution") or data.get("attribution")),
        "rights": _text(data.get("source_rights") or data.get("rights")),
        "url": primary,
        "manifest_url": manifest,
        "image_url": source if kind == "image" else "",
        "pages": _page_map(data),
    }
