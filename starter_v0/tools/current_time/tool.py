from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone as dt_timezone
from typing import Any
from zoneinfo import ZoneInfo

from tools._shared import err

DEFAULT_TIMEZONE = "Asia/Ho_Chi_Minh"
WEEKDAYS_VI = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"]

# Used when the OS has no IANA timezone database (common on Windows without `tzdata`).
_FIXED_OFFSETS = {"Asia/Ho_Chi_Minh": 7, "Asia/Saigon": 7, "Asia/Bangkok": 7, "UTC": 0, "GMT": 0}
_OFFSET_RE = re.compile(r"^(?:UTC|GMT)\s*([+-])\s*(\d{1,2})(?::?(\d{2}))?$", re.IGNORECASE)


def _now_utc() -> datetime:
    """Current UTC time. Tests replace this function to get a fixed clock."""
    return datetime.now(dt_timezone.utc)


def _resolve_timezone(name: str):
    name = (name or "").strip() or DEFAULT_TIMEZONE
    match = _OFFSET_RE.match(name)
    if match:
        sign = 1 if match.group(1) == "+" else -1
        hours, minutes = int(match.group(2)), int(match.group(3) or 0)
        if hours > 14 or minutes > 59:
            raise ValueError(f"UTC offset out of range: {name!r}")
        return dt_timezone(sign * timedelta(hours=hours, minutes=minutes), name=f"UTC{match.group(1)}{hours:02d}:{minutes:02d}")
    try:
        return ZoneInfo(name)
    except Exception:
        if name in _FIXED_OFFSETS:
            return dt_timezone(timedelta(hours=_FIXED_OFFSETS[name]), name=name)
        raise ValueError(f"Unknown timezone {name!r}. Use an IANA name like 'Asia/Ho_Chi_Minh' or an offset like 'UTC+7'.")


def get_current_time(timezone: str = DEFAULT_TIMEZONE) -> dict[str, Any]:
    """Return the current date and time in the requested timezone. Never raises."""
    try:
        tz = _resolve_timezone(timezone)
        now = _now_utc().astimezone(tz)
        offset = now.utcoffset() or timedelta(0)
        total_minutes = int(offset.total_seconds() // 60)
        sign = "+" if total_minutes >= 0 else "-"
        offset_text = f"{sign}{abs(total_minutes) // 60:02d}:{abs(total_minutes) % 60:02d}"
        return {
            "tool": "get_current_time",
            "timezone": (timezone or DEFAULT_TIMEZONE).strip() or DEFAULT_TIMEZONE,
            "iso": now.isoformat(timespec="seconds"),
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M"),
            "weekday_vi": WEEKDAYS_VI[now.weekday()],
            "weekday_en": now.strftime("%A"),
            "utc_offset": offset_text,
        }
    except Exception as exc:
        return err("get_current_time", exc)
