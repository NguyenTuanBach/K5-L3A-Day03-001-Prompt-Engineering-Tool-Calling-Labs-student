from __future__ import annotations

from typing import Any
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from tools._shared import err, fold_text

_TRACKING_PARAMS = {"fbclid", "gclid", "ref", "ref_src", "igshid", "mc_cid", "mc_eid"}


def _normalize_url(url: str) -> str:
    """Canonical form of a URL so that trivially different links compare equal."""
    parsed = urlparse(url.strip())
    host = parsed.netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    query = [
        (key, value) for key, value in parse_qsl(parsed.query, keep_blank_values=True)
        if not key.lower().startswith("utm_") and key.lower() not in _TRACKING_PARAMS
    ]
    path = parsed.path.rstrip("/")
    return urlunparse((parsed.scheme.lower(), host, path, "", urlencode(query), ""))


def _item_key(item: dict[str, Any]) -> str:
    url = (item.get("url") or "").strip()
    if url:
        return "url:" + _normalize_url(url)
    title = fold_text((item.get("title") or "").strip())
    return "title:" + " ".join(title.split()) if title else ""


def dedupe_items(items: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Remove duplicate items (same normalized URL, or same title when there is no URL).

    Keeps the first occurrence and the original order. Never raises: bad input
    returns an error dict like the other tools.
    """
    try:
        if items is None:
            items = []
        if not isinstance(items, list):
            raise TypeError(f"items must be a list of objects, got {type(items).__name__}")

        seen: set[str] = set()
        unique: list[dict[str, Any]] = []
        duplicates: list[dict[str, Any]] = []
        for item in items:
            if not isinstance(item, dict):
                duplicates.append({"title": str(item), "url": "", "reason": "not_an_object"})
                continue
            key = _item_key(item)
            if key and key in seen:
                duplicates.append({"title": item.get("title"), "url": item.get("url"), "reason": "duplicate"})
                continue
            if key:
                seen.add(key)
            unique.append(item)
        return {
            "tool": "dedupe_items",
            "items": unique,
            "item_count": len(unique),
            "removed_count": len(duplicates),
            "removed": duplicates,
        }
    except Exception as exc:
        return err("dedupe_items", exc)
