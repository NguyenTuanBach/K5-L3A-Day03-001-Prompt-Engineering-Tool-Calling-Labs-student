from __future__ import annotations

from datetime import date
from typing import Any


def _parse(value: str) -> date:
    return date.fromisoformat(value.strip())


def date_diff(start_date: str = "", end_date: str = "") -> dict[str, Any]:
    if not isinstance(start_date, str) or not isinstance(end_date, str):
        return {"error": "ValueError", "message": "start_date and end_date must be strings"}
    try:
        start, end = _parse(start_date), _parse(end_date)
    except ValueError:
        return {"error": "ValueError", "message": "dates must use YYYY-MM-DD and be valid calendar dates"}
    days = (end - start).days
    return {
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "days": days,
        "weeks": round(days / 7, 2),
    }
