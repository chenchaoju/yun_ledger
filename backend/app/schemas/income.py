from __future__ import annotations

from datetime import date
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ExtraIncomeItem(BaseModel):
    name: str = Field(default="额外收入", min_length=1, max_length=60)
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    occurred_at: date | None = None

    @field_validator("name", mode="before")
    @classmethod
    def clean_name(cls, value) -> str:
        return str(value or "额外收入").strip() or "额外收入"


class ExtraIncomeItemRead(BaseModel):
    name: str
    amount: float
    occurred_at: date | None = None


class MonthlyIncomeUpsert(BaseModel):
    year: int = Field(ge=1970, le=2100)
    month: int = Field(ge=1, le=12)
    salary_income: Decimal = Field(default=0, ge=0, max_digits=12, decimal_places=2)
    extra_income: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    extra_income_items: list[ExtraIncomeItem] = Field(default_factory=list)


class MonthlyIncomeBase(MonthlyIncomeUpsert):
    pass


class MonthlyIncomeRead(BaseModel):
    id: int | None = None
    user_id: int
    year: int
    month: int
    salary_income: float
    extra_income: float
    extra_income_items: list[ExtraIncomeItemRead] = Field(default_factory=list)
    total_income: float
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
