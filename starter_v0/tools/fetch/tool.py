from __future__ import annotations

import ipaddress
import os
import re
from html.parser import HTMLParser
from typing import Any
from urllib.parse import urlparse

import requests

from tools._shared import TIMEOUT, domain, err

MAX_SUMMARY_CHARS = 4000
MAX_DOWNLOAD_BYTES = 1_000_000
_SKIP_TAGS = {"script", "style", "noscript", "svg", "head"}


class _TextExtractor(HTMLParser):
    """Tiny HTML -> text converter (stdlib only): drops scripts/styles, keeps <title>."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title = ""
        self._in_title = False
        self._skip = 0
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list) -> None:
        if tag == "title":
            self._in_title = True
        elif tag in _SKIP_TAGS:
            self._skip += 1
        elif tag in {"p", "div", "br", "li", "tr", "h1", "h2", "h3", "h4"}:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._in_title = False
        elif tag in _SKIP_TAGS and self._skip:
            self._skip -= 1

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.title += data
        elif not self._skip:
            self.parts.append(data)


def html_to_text(raw_html: str) -> tuple[str, str]:
    parser = _TextExtractor()
    parser.feed(raw_html)
    text = re.sub(r"[ \t\r\f\v]+", " ", "".join(parser.parts))
    text = re.sub(r"\s*\n\s*", "\n", text).strip()
    return parser.title.strip(), text


def check_public_http_url(url: str) -> None:
    """Refuse non-http(s) URLs and obvious local/private hosts (IP literals, localhost).

    Limitation: hostnames are not resolved, so a public name that points to a private IP is not caught.
    """
    parsed = urlparse(url.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("Only http(s) URLs are allowed")
    host = parsed.hostname.lower()
    if host == "localhost" or host.endswith(".local") or host.endswith(".internal"):
        raise ValueError("Local addresses are not allowed")
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        return  # a normal hostname
    if not address.is_global:
        raise ValueError("Private or local IP addresses are not allowed")


def _firecrawl(url: str) -> dict[str, Any]:
    key = os.getenv("FIRECRAWL_API_KEY")
    if not key:
        raise RuntimeError("Missing FIRECRAWL_API_KEY env var")
    response = requests.post(
        "https://api.firecrawl.dev/v1/scrape",
        json={"url": url, "formats": ["markdown"]},
        headers={"Authorization": f"Bearer {key}"},
        timeout=60,
    )
    response.raise_for_status()
    data = response.json().get("data", {})
    meta = data.get("metadata", {}) or {}
    return {"tool": "read_url", "url": url, "items": [{
        "title": meta.get("title") or url,
        "url": meta.get("sourceURL") or url,
        "source": domain(url),
        "summary": (data.get("markdown") or "")[:MAX_SUMMARY_CHARS],
    }]}


def _direct(url: str) -> dict[str, Any]:
    check_public_http_url(url)
    response = requests.get(
        url,
        headers={"User-Agent": "Mozilla/5.0 (compatible; ResearchAgent/1.0)"},
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    title, text = html_to_text(response.text[:MAX_DOWNLOAD_BYTES])
    if not text:
        raise ValueError("Page has no readable text")
    return {"tool": "read_url", "url": url, "via": "direct_fallback", "items": [{
        "title": title or url,
        "url": url,
        "source": domain(url),
        "summary": text[:MAX_SUMMARY_CHARS],
    }]}


def read_url(url: str = "") -> dict[str, Any]:
    try:
        return _firecrawl(url)
    except Exception as firecrawl_exc:
        # Firecrawl can fail for a specific site (HTTP 500, blocked). Try a plain download once.
        try:
            return _direct(url)
        except Exception as direct_exc:
            result = err("read_url", firecrawl_exc)
            result["fallback_error"] = f"{type(direct_exc).__name__}: {direct_exc}"
            return result
