from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.expense import Expense
from app.models.monthly_income import MonthlyIncome
from app.models.user import User
from app.schemas.expense import ExpenseBase
from app.schemas.income import ExtraIncomeItem
from app.services.income_items import extra_income_total, normalize_extra_income_items

router = APIRouter(prefix="/data", tags=["data"])


class DataTransferExpense(ExpenseBase):
    pass


class DataTransferMonthlyIncome(BaseModel):
    year: int = Field(ge=1970, le=2100)
    month: int = Field(ge=1, le=12)
    salary_income: Decimal = Field(default=0, ge=0, max_digits=12, decimal_places=2)
    extra_income: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    extra_income_items: list[ExtraIncomeItem] = Field(default_factory=list)


class DataTransferPayload(BaseModel):
    version: int = 1
    exported_at: datetime | None = None
    expenses: list[DataTransferExpense] = Field(default_factory=list)
    monthly_incomes: list[DataTransferMonthlyIncome] = Field(default_factory=list)


class DataImportResult(BaseModel):
    expenses: int
    monthly_incomes: int


@router.get("/export", response_model=DataTransferPayload)
def export_data(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DataTransferPayload:
    expenses = db.scalars(
        select(Expense)
        .where(Expense.user_id == current_user.id)
        .order_by(Expense.spent_at.asc(), Expense.id.asc())
    ).all()
    monthly_incomes = db.scalars(
        select(MonthlyIncome)
        .where(MonthlyIncome.user_id == current_user.id)
        .order_by(MonthlyIncome.year.asc(), MonthlyIncome.month.asc())
    ).all()

    return DataTransferPayload(
        version=1,
        exported_at=datetime.now(timezone.utc),
        expenses=[
            DataTransferExpense(
                amount=expense.amount,
                category=expense.category,
                note=expense.note,
                spent_at=expense.spent_at,
            )
            for expense in expenses
        ],
        monthly_incomes=[
            DataTransferMonthlyIncome(
                year=income.year,
                month=income.month,
                salary_income=income.salary_income,
                extra_income=income.extra_income,
                extra_income_items=normalize_extra_income_items(income.extra_income_items, income.extra_income),
            )
            for income in monthly_incomes
        ],
    )


@router.post("/import", response_model=DataImportResult)
def import_data(
    payload: DataTransferPayload,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DataImportResult:
    if payload.version != 1:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不支持的数据文件版本")

    monthly_income_by_period = {
        (income.year, income.month): income
        for income in payload.monthly_incomes
    }

    try:
        db.execute(delete(Expense).where(Expense.user_id == current_user.id))
        db.execute(delete(MonthlyIncome).where(MonthlyIncome.user_id == current_user.id))

        for expense in payload.expenses:
            db.add(Expense(user_id=current_user.id, **expense.model_dump()))

        for income in monthly_income_by_period.values():
            extra_items = normalize_extra_income_items(income.extra_income_items, income.extra_income)
            db.add(
                MonthlyIncome(
                    user_id=current_user.id,
                    year=income.year,
                    month=income.month,
                    salary_income=income.salary_income,
                    extra_income=extra_income_total(extra_items),
                    extra_income_items=extra_items,
                )
            )

        db.commit()
    except Exception:
        db.rollback()
        raise

    return DataImportResult(expenses=len(payload.expenses), monthly_incomes=len(monthly_income_by_period))
