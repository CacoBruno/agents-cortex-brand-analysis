from __future__ import annotations

from decimal import InvalidOperation
from typing import Any


def _to_float(value: Any) -> float | None:
    if value is None:
        return None

    try:
        if isinstance(value, str):
            value = value.strip().replace("%", "")
            if value == "":
                return None

            # interpreta formato brasileiro
            if "," in value and "." in value:
                value = value.replace(".", "").replace(",", ".")
            elif "," in value:
                value = value.replace(",", ".")

        return float(value)
    except (ValueError, TypeError, InvalidOperation):
        return None


def format_number(
    value: Any,
    decimals: int = 1,
    use_suffix: bool = False,
) -> str:
    """
    Formata número em padrão brasileiro e evita notação científica.

    Exemplos:
    - 2962820 -> '2.962.820'
    - 1234.56 -> '1.234,6'
    - 2962820 com use_suffix=True -> '3,0M'
    """
    num = _to_float(value)
    if num is None:
        return "-"

    if use_suffix:
        abs_num = abs(num)
        if abs_num >= 1_000_000_000:
            return f"{num / 1_000_000_000:.{decimals}f}B".replace(".", ",")
        if abs_num >= 1_000_000:
            return f"{num / 1_000_000:.{decimals}f}M".replace(".", ",")
        if abs_num >= 1_000:
            return f"{num / 1_000:.{decimals}f}K".replace(".", ",")

    if float(num).is_integer():
        return f"{int(num):,}".replace(",", ".")

    formatted = f"{num:,.{decimals}f}"
    return formatted.replace(",", "X").replace(".", ",").replace("X", ".")


def format_percentage(
    value: Any,
    decimals: int = 1,
    input_already_percent: bool = False,
) -> str:
    """
    Formata percentual em padrão brasileiro.

    Exemplos:
    - 0.123 -> '12,3%'
    - 12.3 com input_already_percent=True -> '12,3%'
    """
    num = _to_float(value)
    if num is None:
        return "-"

    if not input_already_percent:
        num *= 100

    return f"{num:.{decimals}f}%".replace(".", ",")