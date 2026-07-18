from __future__ import annotations

from calendar import monthrange
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal

from app.models.recurring_expense import RecurringExpense


@dataclass
class RecurringExpenseOccurrence:
    id: str
    source_id: int
    name: str
    amount: Decimal
    category: str
    record_date: date
    created_at: datetime | None = None
    updated_at: datetime | None = None


def occurrence_date(item: RecurringExpense, year: int, month: int) -> date | None:
    if not item.enabled:
        return None
    if item.frequency == "yearly" and item.month_of_year != month:
        return None

    day = min(int(item.day_of_month or 1), monthrange(year, month)[1])
    current_date = date(year, month, day)
    effective_start = item.start_date or (item.created_at.date() if item.created_at else None)
    if effective_start and current_date < effective_start:
        return None
    return current_date


def recurring_occurrences_between(
    items: list[RecurringExpense],
    start_date: date,
    end_date: date,
) -> list[RecurringExpenseOccurrence]:
    occurrences: list[RecurringExpenseOccurrence] = []
    year = start_date.year
    month = start_date.month

    while (year, month) <= (end_date.year, end_date.month):
        for item in items:
            current_date = occurrence_date(item, year, month)
            if current_date is None or current_date < start_date or current_date > end_date:
                continue
            occurrences.append(
                RecurringExpenseOccurrence(
                    id=f"recurring-{item.id}-{current_date.isoformat()}",
                    source_id=item.id,
                    name=item.name,
                    amount=item.amount,
                    category=item.category,
                    record_date=current_date,
                    created_at=item.created_at,
                    updated_at=item.updated_at,
                )
            )

        month += 1
        if month > 12:
            year += 1
            month = 1

    return occurrences
