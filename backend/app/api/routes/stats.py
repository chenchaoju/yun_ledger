from __future__ import annotations

from calendar import monthrange
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy import extract, func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.expense import Expense
from app.models.monthly_income import MonthlyIncome
from app.models.recurring_expense import RecurringExpense
from app.models.user import User
from app.schemas.stats import (
    CategorySummary,
    DailyExpensePoint,
    ExtraIncomeSummary,
    MonthlyIncomeSummary,
    OverviewStats,
    StructureSummary,
    TrendPoint,
)
from app.services.income_items import extra_income_total, normalize_extra_income_items
from app.services.recurring_expenses import recurring_occurrences_between

router = APIRouter(prefix="/stats", tags=["stats"])


def to_float(value) -> float:
    return round(float(value or 0), 2)


@router.get("/overview", response_model=OverviewStats)
def overview(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    year: int | None = Query(default=None, ge=1970, le=2100),
    month: int | None = Query(default=None, ge=1, le=12),
) -> OverviewStats:
    today = date.today()
    selected_year = year or today.year
    selected_month = month or today.month
    days_in_month = monthrange(selected_year, selected_month)[1]

    month_start = date(selected_year, selected_month, 1)
    month_end = date(selected_year, selected_month, days_in_month)
    year_start = date(selected_year, 1, 1)
    year_end = date(selected_year, 12, 31)
    opening_amount = to_float(current_user.opening_balance_amount)
    effective_month_start = month_start
    effective_year_start = year_start
    month_in_scope = True
    year_in_scope = True
    recurring_items = list(db.scalars(select(RecurringExpense).where(RecurringExpense.user_id == current_user.id)).all())

    month_total = (
        db.scalar(
            select(func.coalesce(func.sum(Expense.amount), 0)).where(
                Expense.user_id == current_user.id,
                Expense.spent_at >= effective_month_start,
                Expense.spent_at <= month_end,
            )
        )
        if month_in_scope
        else 0
    )
    manual_month_count = (
        db.scalar(
            select(func.count()).select_from(Expense).where(
                Expense.user_id == current_user.id,
                Expense.spent_at >= effective_month_start,
                Expense.spent_at <= month_end,
            )
        )
        or 0
        if month_in_scope
        else 0
    )
    month_recurring_end = min(month_end, today)
    month_recurring = (
        recurring_occurrences_between(recurring_items, effective_month_start, month_recurring_end)
        if effective_month_start <= today
        else []
    )
    recurring_month_total = sum((item.amount for item in month_recurring), start=0)
    year_total = (
        db.scalar(
            select(func.coalesce(func.sum(Expense.amount), 0)).where(
                Expense.user_id == current_user.id,
                Expense.spent_at >= effective_year_start,
                Expense.spent_at <= year_end,
            )
        )
        if year_in_scope
        else 0
    )
    manual_year_months = {
        int(row.month)
        for row in db.execute(
            select(extract("month", Expense.spent_at).label("month"))
            .where(
                Expense.user_id == current_user.id,
                Expense.spent_at >= effective_year_start,
                Expense.spent_at <= year_end,
            )
            .group_by(extract("month", Expense.spent_at))
        ).all()
    } if year_in_scope else set()
    year_recurring = (
        recurring_occurrences_between(recurring_items, effective_year_start, min(year_end, today))
        if year_in_scope and effective_year_start <= today
        else []
    )
    recurring_year_months = {occurrence.record_date.month for occurrence in year_recurring}
    recurring_year_total = sum((item.amount for item in year_recurring), start=0)
    year_count = (
        db.scalar(
            select(func.count()).select_from(Expense).where(
                Expense.user_id == current_user.id,
                Expense.spent_at >= effective_year_start,
                Expense.spent_at <= year_end,
            )
        )
        or 0
    ) + len(year_recurring) if year_in_scope else 0
    month_count = manual_month_count + len(month_recurring)

    category_rows = (
        db.execute(
            select(
                Expense.category,
                func.coalesce(func.sum(Expense.amount), 0).label("total"),
                func.count(Expense.id).label("count"),
            )
            .where(
                Expense.user_id == current_user.id,
                Expense.spent_at >= effective_month_start,
                Expense.spent_at <= month_end,
            )
            .group_by(Expense.category)
            .order_by(func.sum(Expense.amount).desc())
        )
        .all()
        if month_in_scope
        else []
    )

    month_expr = extract("month", Expense.spent_at)
    trend_rows = (
        db.execute(
            select(
                month_expr.label("month"),
                func.coalesce(func.sum(Expense.amount), 0).label("total"),
            )
            .where(
                Expense.user_id == current_user.id,
                Expense.spent_at >= effective_year_start,
                Expense.spent_at <= year_end,
            )
            .group_by(month_expr)
            .order_by(month_expr)
        )
        .all()
        if year_in_scope
        else []
    )
    trend_map = {int(row.month): to_float(row.total) for row in trend_rows}
    for occurrence in year_recurring:
        trend_map[occurrence.record_date.month] = round(
            trend_map.get(occurrence.record_date.month, 0) + to_float(occurrence.amount),
            2,
        )

    income_rows = db.scalars(
        select(MonthlyIncome).where(
            MonthlyIncome.user_id == current_user.id,
            MonthlyIncome.year == selected_year,
        )
    ).all()
    default_salary_income = to_float(current_user.default_salary_income)
    income_map = {}
    for income in income_rows:
        extra_items = normalize_extra_income_items(income.extra_income_items, income.extra_income)
        mapped_salary_income = to_float(income.salary_income) or default_salary_income
        mapped_extra_income = to_float(extra_income_total(extra_items))
        income_map[income.month] = {
            "salary_income": mapped_salary_income,
            "extra_income": mapped_extra_income,
            "extra_income_items": extra_items,
            "total_income": round(mapped_salary_income + mapped_extra_income, 2),
        }

    def iter_months(start_date: date, end_date: date):
        cursor_year = start_date.year
        cursor_month = start_date.month
        while (cursor_year, cursor_month) <= (end_date.year, end_date.month):
            yield cursor_year, cursor_month
            if cursor_month == 12:
                cursor_year += 1
                cursor_month = 1
            else:
                cursor_month += 1

    def build_total_balance_points(end_date: date) -> tuple[dict[tuple[int, int], float | None], float]:
        balance_reset_at = current_user.opening_balance_reset_at
        balance_start = balance_reset_at.date() if balance_reset_at else date(1970, 1, 1)
        if end_date < balance_start:
            return {}, opening_amount

        balance_year_expr = extract("year", Expense.spent_at)
        balance_month_expr = extract("month", Expense.spent_at)
        balance_expense_filters = [
            Expense.user_id == current_user.id,
            Expense.spent_at >= balance_start,
            Expense.spent_at <= end_date,
        ]
        if balance_reset_at:
            balance_expense_filters.append(Expense.created_at >= balance_reset_at)
        balance_expense_rows = db.execute(
            select(
                balance_year_expr.label("year"),
                balance_month_expr.label("month"),
                func.coalesce(func.sum(Expense.amount), 0).label("total"),
            )
            .where(*balance_expense_filters)
            .group_by(balance_year_expr, balance_month_expr)
        ).all()
        expense_map = {
            (int(row.year), int(row.month)): to_float(row.total)
            for row in balance_expense_rows
        }
        expense_months = set(expense_map)

        recurring_map: dict[tuple[int, int], float] = {}
        for occurrence in recurring_occurrences_between(recurring_items, balance_start, end_date):
            if balance_reset_at and occurrence.record_date <= balance_start:
                continue
            key = (occurrence.record_date.year, occurrence.record_date.month)
            recurring_map[key] = round(recurring_map.get(key, 0) + to_float(occurrence.amount), 2)
        expense_months.update(recurring_map)

        balance_income_filters = [
            MonthlyIncome.user_id == current_user.id,
            MonthlyIncome.year >= balance_start.year,
            MonthlyIncome.year <= end_date.year,
        ]
        if balance_reset_at:
            balance_income_filters.append(MonthlyIncome.updated_at >= balance_reset_at)
        balance_income_rows = db.scalars(
            select(MonthlyIncome).where(*balance_income_filters)
        ).all()
        balance_income_map = {}
        for income in balance_income_rows:
            current_month_start = date(income.year, income.month, 1)
            current_month_end = date(income.year, income.month, monthrange(income.year, income.month)[1])
            if current_month_end < balance_start or current_month_start > end_date:
                continue
            extra_items = normalize_extra_income_items(income.extra_income_items, income.extra_income)
            mapped_salary_income = to_float(income.salary_income) or default_salary_income
            mapped_extra_income = to_float(extra_income_total(extra_items))
            balance_income_map[(income.year, income.month)] = round(mapped_salary_income + mapped_extra_income, 2)

        running_balance = opening_amount
        points: dict[tuple[int, int], float | None] = {}
        for balance_year, balance_month in iter_months(balance_start, end_date):
            key = (balance_year, balance_month)
            month_start_for_balance = date(balance_year, balance_month, 1)
            has_expense = key in expense_months
            has_income_record = key in balance_income_map
            is_reset_month = bool(
                balance_reset_at
                and balance_reset_at.year == balance_year
                and balance_reset_at.month == balance_month
            )
            should_apply_default_salary = has_expense and (
                not balance_reset_at or month_start_for_balance > date(balance_reset_at.year, balance_reset_at.month, 1)
            )
            income_amount = balance_income_map.get(key, default_salary_income if should_apply_default_salary else 0)
            expense_amount = round(expense_map.get(key, 0) + recurring_map.get(key, 0), 2)
            if has_expense or has_income_record or is_reset_month:
                if is_reset_month and balance_reset_at and not has_expense and not has_income_record:
                    points[key] = running_balance
                    continue
                running_balance = round(
                    running_balance
                    + income_amount
                    - expense_amount,
                    2,
                )
                points[key] = running_balance
            else:
                points[key] = None

        return points, running_balance

    if month_in_scope:
        selected_income = income_map.get(
            selected_month,
            {
                "salary_income": default_salary_income,
                "extra_income": 0,
                "extra_income_items": [],
                "total_income": default_salary_income,
            },
        )
    else:
        selected_income = {
            "salary_income": 0,
            "extra_income": 0,
            "extra_income_items": [],
            "total_income": 0,
        }
    salary_income = selected_income["salary_income"]
    extra_income = selected_income["extra_income"]
    extra_income_items = selected_income["extra_income_items"]
    total_income = round(salary_income + extra_income, 2)
    month_total_float = round(to_float(month_total) + to_float(recurring_month_total), 2)
    salary_balance = round(salary_income - month_total_float, 2)
    balance = round(total_income - month_total_float, 2)
    category_summary_map = {row.category: {"total": to_float(row.total), "count": row.count} for row in category_rows}
    for occurrence in month_recurring:
        summary = category_summary_map.setdefault(occurrence.category, {"total": 0, "count": 0})
        summary["total"] = round(summary["total"] + to_float(occurrence.amount), 2)
        summary["count"] += 1
    structure_summary = [
        StructureSummary(name=category, type="支出", total=value["total"], count=value["count"])
        for category, value in sorted(category_summary_map.items(), key=lambda item: item[1]["total"], reverse=True)
    ]

    day_expr = extract("day", Expense.spent_at)
    daily_rows = (
        db.execute(
            select(
                day_expr.label("day"),
                func.coalesce(func.sum(Expense.amount), 0).label("total"),
            )
            .where(
                Expense.user_id == current_user.id,
                Expense.spent_at >= effective_month_start,
                Expense.spent_at <= month_end,
            )
            .group_by(day_expr)
            .order_by(day_expr)
        )
        .all()
        if month_in_scope
        else []
    )
    daily_map = {int(row.day): to_float(row.total) for row in daily_rows}
    for occurrence in month_recurring:
        daily_map[occurrence.record_date.day] = round(
            daily_map.get(occurrence.record_date.day, 0) + to_float(occurrence.amount),
            2,
        )

    recent_expenses = db.scalars(
        select(Expense)
        .where(Expense.user_id == current_user.id)
        .order_by(Expense.spent_at.desc(), Expense.id.desc())
        .limit(6)
    ).all()

    if not month_in_scope:
        average_basis = 1
    else:
        average_end_day = today.day if selected_year == today.year and selected_month == today.month else days_in_month
        average_basis = max(average_end_day - effective_month_start.day + 1, 1)

    def trend_income(month_index: int) -> dict:
        return {
            "salary_income": income_map.get(month_index, {}).get("salary_income", default_salary_income),
            "extra_income": income_map.get(month_index, {}).get("extra_income", 0),
            "total_income": income_map.get(month_index, {}).get("total_income", default_salary_income),
        }

    selected_balance_end = min(month_end, today) if month_end >= today else month_end
    annual_balance_end = year_end if selected_year < today.year else min(year_end, today)
    total_balance_points, current_total_balance = build_total_balance_points(max(selected_balance_end, annual_balance_end))

    return OverviewStats(
        month_total=month_total_float,
        year_total=round(to_float(year_total) + to_float(recurring_year_total), 2),
        total_balance=current_total_balance,
        year_count=year_count,
        month_count=month_count,
        average_day=round(month_total_float / max(average_basis, 1), 2),
        monthly_income=MonthlyIncomeSummary(
            year=selected_year,
            month=selected_month,
            salary_income=salary_income,
            extra_income=extra_income,
            extra_income_items=[
                ExtraIncomeSummary(name=item["name"], amount=to_float(item["amount"])) for item in extra_income_items
            ],
            total_income=total_income,
            balance=balance,
            salary_balance=salary_balance,
            is_over_salary=salary_income > 0 and month_total_float > salary_income,
        ),
        category_summary=[
            CategorySummary(category=category, total=value["total"], count=value["count"])
            for category, value in sorted(category_summary_map.items(), key=lambda item: item[1]["total"], reverse=True)
        ],
        structure_summary=structure_summary,
        monthly_trend=[
            TrendPoint(
                month=index,
                total=trend_map.get(index, 0),
                salary_income=trend_income(index)["salary_income"],
                extra_income=trend_income(index)["extra_income"],
                total_income=trend_income(index)["total_income"],
                balance=round(
                    trend_income(index)["total_income"]
                    - trend_map.get(index, 0),
                    2,
                ),
                total_balance=total_balance_points.get((selected_year, index)),
                has_expense=index in manual_year_months or index in recurring_year_months,
                is_over_salary=(
                    trend_income(index)["salary_income"] > 0
                    and trend_map.get(index, 0) > trend_income(index)["salary_income"]
                ),
            )
            for index in range(1, 13)
        ],
        daily_expenses=[
            DailyExpensePoint(day=index, total=daily_map.get(index, 0)) for index in range(1, days_in_month + 1)
        ],
        recent_expenses=list(recent_expenses),
    )
