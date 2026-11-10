from __future__ import annotations

from tools.unit_convert.tool import unit_convert
from tools.date_diff.tool import date_diff


def test_unit_convert_rejects_bool_value() -> None:
    assert unit_convert(value=True, from_unit="m", to_unit="m")["error"] == "ValueError"


def test_date_diff_end_before_start_returns_negative_days() -> None:
    assert date_diff(start_date="2026-11-10", end_date="2026-11-01")["days"] == -9
