from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.monthly_income import MonthlyIncome
from app.models.user import User
from app.schemas.income import ExtraIncomeItemRead, MonthlyIncomeRead, MonthlyIncomeUpsert
from app.services.income_items import extra_income_total, normalize_extra_income_items

router = APIRouter(prefix="/incomes", tags=["incomes"])


def to_float(value) -> float:
    return round(float(value or 0), 2)


def read_or_default(user: User, year: int, month: int, db: Session) -> MonthlyIncomeRead:
    income = db.scalar(
        select(MonthlyIncome).where(
            MonthlyIncome.user_id == user.id,
            MonthlyIncome.year == year,
            MonthlyIncome.month == month,
        )
    )
    default_salary_income = to_float(user.default_salary_income)

    if income is None:
        return MonthlyIncomeRead(
            id=None,
            user_id=user.id,
            year=year,
            month=month,
            salary_income=default_salary_income,
            extra_income=0,
            extra_income_items=[],
            total_income=default_salary_income,
        )

    extra_items = normalize_extra_income_items(income.extra_income_items, income.extra_income)
    salary_income = to_float(income.salary_income) or default_salary_income
    extra_income = to_float(extra_income_total(extra_items))

    return MonthlyIncomeRead(
        id=income.id,
        user_id=income.user_id,
        year=income.year,
        month=income.month,
        salary_income=salary_income,
        extra_income=extra_income,
        extra_income_items=[ExtraIncomeItemRead(**item) for item in extra_items],
        total_income=round(salary_income + extra_income, 2),
        created_at=income.created_at,
        updated_at=income.updated_at,
    )


@router.get("/monthly", response_model=MonthlyIncomeRead)
def get_monthly_income(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    year: int = Query(ge=1970, le=2100),
    month: int = Query(ge=1, le=12),
) -> MonthlyIncomeRead:
    return read_or_default(current_user, year, month, db)


@router.put("/monthly", response_model=MonthlyIncomeRead)
def upsert_monthly_income(
    payload: MonthlyIncomeUpsert,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MonthlyIncomeRead:
    extra_items = normalize_extra_income_items(payload.extra_income_items, payload.extra_income)
    extra_income = extra_income_total(extra_items)

    income = db.scalar(
        select(MonthlyIncome).where(
            MonthlyIncome.user_id == current_user.id,
            MonthlyIncome.year == payload.year,
            MonthlyIncome.month == payload.month,
        )
    )

    if income is None:
        income = MonthlyIncome(
            user_id=current_user.id,
            year=payload.year,
            month=payload.month,
            salary_income=payload.salary_income,
            extra_income=extra_income,
            extra_income_items=extra_items,
        )
    else:
        income.salary_income = payload.salary_income
        income.extra_income = extra_income
        income.extra_income_items = extra_items

    db.add(income)
    db.commit()
    db.refresh(income)
    return read_or_default(current_user, payload.year, payload.month, db)
