from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.category_preference import CategoryPreference
from app.models.expense import Expense
from app.models.monthly_income import MonthlyIncome
from app.models.recurring_expense import RecurringExpense
from app.models.user import User
from app.schemas.expense import ExpenseBase
from app.schemas.income import ExtraIncomeItem
from app.schemas.category import CategoryPreferenceBase
from app.schemas.recurring_expense import RecurringExpenseBase
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


class DataTransferRecurringExpense(RecurringExpenseBase):
    pass


class DataTransferPayload(BaseModel):
    version: int = 1
    exported_at: datetime | None = None
    expenses: list[DataTransferExpense] = Field(default_factory=list)
    monthly_incomes: list[DataTransferMonthlyIncome] = Field(default_factory=list)
    recurring_expenses: list[DataTransferRecurringExpense] = Field(default_factory=list)
    category_preference: CategoryPreferenceBase | None = None


class DataImportResult(BaseModel):
    expenses: int
    monthly_incomes: int
    recurring_expenses: int
    category_preference: bool = False


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
    recurring_expenses = db.scalars(
        select(RecurringExpense)
        .where(RecurringExpense.user_id == current_user.id)
        .order_by(RecurringExpense.enabled.desc(), RecurringExpense.id.asc())
    ).all()
    category_preference = db.scalar(select(CategoryPreference).where(CategoryPreference.user_id == current_user.id))

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
        recurring_expenses=[
            DataTransferRecurringExpense(
                name=item.name,
                amount=item.amount,
                category=item.category,
                frequency=item.frequency,
                day_of_month=item.day_of_month,
                month_of_year=item.month_of_year,
                start_date=item.start_date,
                enabled=item.enabled,
            )
            for item in recurring_expenses
        ],
        category_preference=CategoryPreferenceBase(
            custom_categories=category_preference.custom_categories,
            hidden_category_values=category_preference.hidden_category_values,
            category_order=category_preference.category_order,
            category_colors=category_preference.category_colors,
        )
        if category_preference
        else None,
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
        db.execute(delete(RecurringExpense).where(RecurringExpense.user_id == current_user.id))
        db.execute(delete(CategoryPreference).where(CategoryPreference.user_id == current_user.id))

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

        for item in payload.recurring_expenses:
            db.add(RecurringExpense(user_id=current_user.id, **item.model_dump()))

        if payload.category_preference:
            db.add(
                CategoryPreference(
                    user_id=current_user.id,
                    custom_categories=[item.model_dump() for item in payload.category_preference.custom_categories],
                    hidden_category_values=payload.category_preference.hidden_category_values,
                    category_order=payload.category_preference.category_order,
                    category_colors=payload.category_preference.category_colors,
                )
            )

        db.commit()
    except Exception:
        db.rollback()
        raise

    return DataImportResult(
        expenses=len(payload.expenses),
        monthly_incomes=len(monthly_income_by_period),
        recurring_expenses=len(payload.recurring_expenses),
        category_preference=payload.category_preference is not None,
    )
