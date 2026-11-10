from __future__ import annotations

from typing import Any

LENGTH = {"m": 1.0, "km": 1000.0, "cm": 0.01, "mm": 0.001, "mi": 1609.344, "ft": 0.3048, "in": 0.0254}
MASS = {"kg": 1.0, "g": 0.001, "mg": 0.000001, "lb": 0.45359237, "oz": 0.028349523125}
TEMP = {"c", "f", "k"}


def _temp_to_c(value: float, unit: str) -> float:
    if unit == "c":
        return value
    if unit == "f":
        return (value - 32) * 5 / 9
    return value - 273.15


def _c_to_temp(value: float, unit: str) -> float:
    if unit == "c":
        return value
    if unit == "f":
        return value * 9 / 5 + 32
    return value + 273.15


def unit_convert(value: float = 0, from_unit: str = "", to_unit: str = "") -> dict[str, Any]:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return {"error": "ValueError", "message": "value must be a number"}
    src, dst = from_unit.strip().lower(), to_unit.strip().lower()
    try:
        if src in TEMP and dst in TEMP:
            result = _c_to_temp(_temp_to_c(float(value), src), dst)
        elif src in LENGTH and dst in LENGTH:
            result = float(value) * LENGTH[src] / LENGTH[dst]
        elif src in MASS and dst in MASS:
            result = float(value) * MASS[src] / MASS[dst]
        else:
            return {"error": "ValueError", "message": f"cannot convert {from_unit!r} to {to_unit!r}"}
    except Exception as exc:
        return {"error": type(exc).__name__, "message": str(exc)}
    return {"value": value, "from_unit": src, "to_unit": dst, "result": round(result, 6)}
