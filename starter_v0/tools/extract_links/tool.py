from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse

from tools._shared import domain, err

# http(s) links, or bare "www." links. Stops at whitespace and common wrapping characters.
_LINK_RE = re.compile(r"(?:https?://|www\.)[^\s<>\"'`]+", re.IGNORECASE)
_TRAILING = ".,;:!?)]}>»”’"
MAX_LINKS = 50


def _clean(raw: str) -> str:
    """Strip punctuation that wraps a link in prose, but keep a ")" that closes a "(" inside the link."""
    link = raw
    while link and link[-1] in _TRAILING:
        if link[-1] == ")" and link.count("(") >= link.count(")"):
            break
        link = link[:-1]
    if link.lower().startswith("www."):
        link = "https://" + link
    return link


def extract_links_from_text(text: str = "") -> dict[str, Any]:
    """Pull the unique URLs out of free text, in order of first appearance. Never raises."""
    try:
        if text is None:
            text = ""
        if not isinstance(text, str):
            raise TypeError(f"text must be a string, got {type(text).__name__}")

        seen: set[str] = set()
        items: list[dict[str, str]] = []
        for match in _LINK_RE.finditer(text):
            link = _clean(match.group(0))
            parsed = urlparse(link)
            if not parsed.netloc or "." not in parsed.netloc:
                continue
            key = link.lower().rstrip("/")
            if key in seen:
                continue
            seen.add(key)
            items.append({"title": link, "url": link, "source": domain(link)})
            if len(items) >= MAX_LINKS:
                break
        return {"tool": "extract_links_from_text", "count": len(items), "items": items}
    except Exception as exc:
        return err("extract_links_from_text", exc)
