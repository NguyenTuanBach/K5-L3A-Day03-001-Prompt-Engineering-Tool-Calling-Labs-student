from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

from tools._shared import domain, err

STYLES = ("markdown", "apa", "plain")


def _require_http_url(url: str) -> str:
    url = (url or "").strip()
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("url must be a full http(s) link")
    return url


def format_citation(title: str = "", url: str = "", author: str = "", date: str = "", style: str = "markdown") -> dict[str, Any]:
    """Build one citation line for a source (the company policy asks for a source URL on every item).

    Styles: markdown -> [Title](url) - Author, date ; apa -> a simplified APA-like line ;
    plain -> Title - domain - url. Never raises: bad input returns an error dict.
    """
    try:
        if style not in STYLES:
            raise ValueError(f"style must be one of {list(STYLES)}, got {style!r}")
        url = _require_http_url(url)
        site = domain(url)
        title = " ".join((title or "").split()) or site
        author = " ".join((author or "").split())
        date = " ".join(str(date or "").split())

        if style == "markdown":
            safe_title = title.replace("[", "(").replace("]", ")")
            extras = ", ".join(part for part in (author, date) if part)
            citation = f"[{safe_title}]({url})" + (f" - {extras}" if extras else "")
        elif style == "apa":
            citation = f"{author or site}. ({date or 'n.d.'}). {title}. {site}. {url}"
        else:
            citation = " - ".join(part for part in (title, site, date, url) if part)
        return {"tool": "format_citation", "style": style, "citation": citation, "source": site}
    except Exception as exc:
        return err("format_citation", exc)
