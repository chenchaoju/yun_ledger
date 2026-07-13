from __future__ import annotations

import calendar
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.expense import Expense
from app.models.recurring_expense import RecurringExpense


def _scheduled_date(rule: RecurringExpense, year: int, month: int) -> date:
    day = min(rule.start_date.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def materialize_recurring_expenses(db: Session, user_id: int, through: date | None = None) -> int:
    through = through or date.today()
    rules = db.scalars(
        select(RecurringExpense).where(
            RecurringExpense.user_id == user_id,
            RecurringExpense.is_active.is_(True),
            RecurringExpense.start_date <= through,
        )
    ).all()
    created = 0

    for rule in rules:
        occurrences: list[date] = []
        if rule.frequency == "yearly":
            for year in range(rule.start_date.year, through.year + 1):
                scheduled = _scheduled_date(rule, year, rule.start_date.month)
                if rule.start_date <= scheduled <= through:
                    occurrences.append(scheduled)
        else:
            year, month = rule.start_date.year, rule.start_date.month
            while (year, month) <= (through.year, through.month):
                scheduled = _scheduled_date(rule, year, month)
                if rule.start_date <= scheduled <= through:
                    occurrences.append(scheduled)
                month += 1
                if month == 13:
                    year, month = year + 1, 1

        existing_periods = set(db.scalars(
            select(Expense.recurring_period).where(Expense.recurring_expense_id == rule.id)
        ).all())
        for scheduled in occurrences:
            period = scheduled.strftime("%Y-%m") if rule.frequency == "monthly" else scheduled.strftime("%Y")
            if period in existing_periods:
                continue
            db.add(Expense(
                user_id=user_id,
                amount=rule.amount,
                category=rule.category,
                note=f"{rule.name}（固定支出）",
                spent_at=scheduled,
                recurring_expense_id=rule.id,
                recurring_period=period,
            ))
            existing_periods.add(period)
            created += 1

    if created:
        db.commit()
    return created
