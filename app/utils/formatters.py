from __future__ import annotations

from typing import Any


def money(value: Any) -> str:
    try:
        number = float(value)
        if number.is_integer():
            return f'{int(number)} ₽'
        return f'{number:.2f} ₽'
    except Exception:
        return f'{value} ₽'


def yes_no(value: Any) -> str:
    return 'Да' if bool(value) else 'Нет'


def pick(*values: Any, default: Any = None) -> Any:
    for value in values:
        if value is not None:
            return value
    return default
