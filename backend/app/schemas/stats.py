from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.expense import ExpenseRead


class CategorySummary(BaseModel):
    category: str
    total: float
    count: int


class StructureSummary(BaseModel):
    name: str
    type: str
    total: float
    count: int


class ExtraIncomeSummary(BaseModel):
    name: str
    amount: float


class TrendPoint(BaseModel):
    month: int
    total: float
    salary_income: float = 0
    extra_income: float = 0
    total_income: float = 0
    balance: float = 0
    total_balance: float | None = None
    has_expense: bool = False
    is_over_salary: bool = False


class DailyExpensePoint(BaseModel):
    day: int
    total: float


class MonthlyIncomeSummary(BaseModel):
    year: int
    month: int
    salary_income: float
    extra_income: float
    extra_income_items: list[ExtraIncomeSummary] = Field(default_factory=list)
    total_income: float
    balance: float
    salary_balance: float
    is_over_salary: bool


class OverviewStats(BaseModel):
    month_total: float
    year_total: float
    total_balance: float = 0
    year_count: int = 0
    month_count: int
    average_day: float
    monthly_income: MonthlyIncomeSummary
    category_summary: list[CategorySummary]
    structure_summary: list[StructureSummary] = Field(default_factory=list)
    monthly_trend: list[TrendPoint]
    daily_expenses: list[DailyExpensePoint]
    recent_expenses: list[ExpenseRead]
