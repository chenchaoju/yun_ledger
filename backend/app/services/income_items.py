from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any

DEFAULT_EXTRA_INCOME_NAME = "额外收入"
AMOUNT_QUANT = Decimal("0.01")


def amount_to_decimal(value: Any) -> Decimal:
    try:
        amount = Decimal(str(value if value is not None else 0))
    except (InvalidOperation, ValueError):
        amount = Decimal("0")
    return amount.quantize(AMOUNT_QUANT, rounding=ROUND_HALF_UP)


def item_value(item: Any, key: str, default: Any = None) -> Any:
    if isinstance(item, dict):
        return item.get(key, default)
    return getattr(item, key, default)


def clean_income_date(value: Any) -> str | None:
    if not value:
        return None
    if isinstance(value, date):
        return value.isoformat()
    text = str(value).strip()
    try:
        return date.fromisoformat(text).isoformat()
    except ValueError:
        return None


def normalize_extra_income_items(items: list[Any] | None, fallback_extra_income: Any = None) -> list[dict[str, float]]:
    normalized: list[dict[str, float]] = []

    for item in items or []:
        name = str(item_value(item, "name", "") or "").strip() or DEFAULT_EXTRA_INCOME_NAME
        amount = amount_to_decimal(item_value(item, "amount", 0))
        if amount <= 0:
            continue
        normalized_item = {"name": name[:60], "amount": float(amount)}
        occurred_at = clean_income_date(item_value(item, "occurred_at"))
        if occurred_at:
            normalized_item["occurred_at"] = occurred_at
        normalized.append(normalized_item)

    if normalized:
        return normalized

    fallback_amount = amount_to_decimal(fallback_extra_income)
    if fallback_amount > 0:
        return [{"name": DEFAULT_EXTRA_INCOME_NAME, "amount": float(fallback_amount)}]

    return []


def extra_income_total(items: list[Any] | None) -> Decimal:
    total = Decimal("0")
    for item in items or []:
        total += amount_to_decimal(item_value(item, "amount", 0))
    return total.quantize(AMOUNT_QUANT, rounding=ROUND_HALF_UP)
