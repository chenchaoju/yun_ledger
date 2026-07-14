from __future__ import annotations

from calendar import monthrange
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy import extract, func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.expense import Expense
from app.models.monthly_income import MonthlyIncome
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
from app.services.recurring_expenses import materialize_recurring_expenses

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
    materialize_recurring_expenses(db, current_user.id, today)
    selected_year = year or today.year
    selected_month = month or today.month
    days_in_month = monthrange(selected_year, selected_month)[1]

    month_start = date(selected_year, selected_month, 1)
    month_end = date(selected_year, selected_month, days_in_month)
    year_start = date(selected_year, 1, 1)
    year_end = date(selected_year, 12, 31)

    month_total = db.scalar(
        select(func.coalesce(func.sum(Expense.amount), 0)).where(
            Expense.user_id == current_user.id,
            Expense.spent_at >= month_start,
            Expense.spent_at <= month_end,
        )
    )
    year_total = db.scalar(
        select(func.coalesce(func.sum(Expense.amount), 0)).where(
            Expense.user_id == current_user.id,
            Expense.spent_at >= year_start,
            Expense.spent_at <= year_end,
        )
    )
    year_count = db.scalar(
        select(func.count()).select_from(Expense).where(
            Expense.user_id == current_user.id,
            Expense.spent_at >= year_start,
            Expense.spent_at <= year_end,
        )
    ) or 0
    month_count = db.scalar(
        select(func.count()).select_from(Expense).where(
            Expense.user_id == current_user.id,
            Expense.spent_at >= month_start,
            Expense.spent_at <= month_end,
        )
    ) or 0

    category_rows = db.execute(
        select(
            Expense.category,
            func.coalesce(func.sum(Expense.amount), 0).label("total"),
            func.count(Expense.id).label("count"),
        )
        .where(
            Expense.user_id == current_user.id,
            Expense.spent_at >= month_start,
            Expense.spent_at <= month_end,
        )
        .group_by(Expense.category)
        .order_by(func.sum(Expense.amount).desc())
    ).all()

    month_expr = extract("month", Expense.spent_at)
    trend_rows = db.execute(
        select(
            month_expr.label("month"),
            func.coalesce(func.sum(Expense.amount), 0).label("total"),
        )
        .where(
            Expense.user_id == current_user.id,
            Expense.spent_at >= year_start,
            Expense.spent_at <= year_end,
        )
        .group_by(month_expr)
        .order_by(month_expr)
    ).all()
    trend_map = {int(row.month): to_float(row.total) for row in trend_rows}

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

    selected_income = income_map.get(
        selected_month,
        {
            "salary_income": default_salary_income,
            "extra_income": 0,
            "extra_income_items": [],
            "total_income": default_salary_income,
        },
    )
    salary_income = selected_income["salary_income"]
    extra_income = selected_income["extra_income"]
    extra_income_items = selected_income["extra_income_items"]
    total_income = round(salary_income + extra_income, 2)
    month_total_float = to_float(month_total)
    salary_balance = round(salary_income - month_total_float, 2)
    balance = round(total_income - month_total_float, 2)
    structure_summary = [
        StructureSummary(name=row.category, type="支出", total=to_float(row.total), count=row.count)
        for row in category_rows
    ]

    day_expr = extract("day", Expense.spent_at)
    daily_rows = db.execute(
        select(
            day_expr.label("day"),
            func.coalesce(func.sum(Expense.amount), 0).label("total"),
        )
        .where(
            Expense.user_id == current_user.id,
            Expense.spent_at >= month_start,
            Expense.spent_at <= month_end,
        )
        .group_by(day_expr)
        .order_by(day_expr)
    ).all()
    daily_map = {int(row.day): to_float(row.total) for row in daily_rows}

    recent_expenses = db.scalars(
        select(Expense)
        .where(Expense.user_id == current_user.id)
        .order_by(Expense.spent_at.desc(), Expense.id.desc())
        .limit(6)
    ).all()

    average_basis = today.day if selected_year == today.year and selected_month == today.month else days_in_month

    return OverviewStats(
        month_total=month_total_float,
        year_total=to_float(year_total),
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
            CategorySummary(category=row.category, total=to_float(row.total), count=row.count)
            for row in category_rows
        ],
        structure_summary=structure_summary,
        monthly_trend=[
            TrendPoint(
                month=index,
                total=trend_map.get(index, 0),
                salary_income=income_map.get(index, {}).get("salary_income", default_salary_income),
                extra_income=income_map.get(index, {}).get("extra_income", 0),
                total_income=income_map.get(index, {}).get("total_income", default_salary_income),
                balance=round(
                    income_map.get(index, {}).get("total_income", default_salary_income) - trend_map.get(index, 0),
                    2,
                ),
                is_over_salary=(
                    income_map.get(index, {}).get("salary_income", default_salary_income) > 0
                    and trend_map.get(index, 0) > income_map.get(index, {}).get("salary_income", default_salary_income)
                ),
            )
            for index in range(1, 13)
        ],
        daily_expenses=[
            DailyExpensePoint(day=index, total=daily_map.get(index, 0)) for index in range(1, days_in_month + 1)
        ],
        recent_expenses=list(recent_expenses),
    )
