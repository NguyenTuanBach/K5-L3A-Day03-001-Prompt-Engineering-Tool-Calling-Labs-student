from __future__ import annotations

from typing import Any


def text_stats(text: str = "", chars_per_minute: int = 1000) -> dict[str, Any]:
    if not isinstance(text, str) or not text.strip():
        return {"error": "ValueError", "message": "text must be a non-empty string"}
    if not isinstance(chars_per_minute, int) or isinstance(chars_per_minute, bool) or chars_per_minute <= 0:
        return {"error": "ValueError", "message": "chars_per_minute must be a positive integer"}
    words = len(text.split())
    characters = len(text)
    return {
        "words": words,
        "characters": characters,
        "reading_minutes": round(characters / chars_per_minute, 1),
    }
