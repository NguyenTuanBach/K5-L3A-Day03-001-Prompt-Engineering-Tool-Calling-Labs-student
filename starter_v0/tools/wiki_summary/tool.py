from __future__ import annotations

import requests

ALLOWED_LANGS = {"vi", "en"}


def wiki_summary(title: str = "", lang: str = "vi") -> dict:
    if not isinstance(title, str) or not title.strip():
        return {"error": "ValueError", "message": "title must be a non-empty string"}
    if lang not in ALLOWED_LANGS:
        return {"error": "ValueError", "message": f"lang must be one of {sorted(ALLOWED_LANGS)}"}

    slug = title.strip().replace(" ", "_")
    url = f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{slug}"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 404:
            return {"error": "NotFound", "message": f"no page for {title!r}"}
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as exc:
        return {"error": type(exc).__name__, "message": str(exc)}

    return {
        "title": data.get("title"),
        "summary": data.get("extract"),
        "url": (data.get("content_urls") or {}).get("desktop", {}).get("page"),
    }
