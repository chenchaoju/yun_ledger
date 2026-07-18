from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class RecurringExpenseBase(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    category: str = Field(min_length=1, max_length=60)
    frequency: Literal["monthly", "yearly"]
    day_of_month: int = Field(ge=1, le=31)
    month_of_year: int | None = Field(default=None, ge=1, le=12)
    start_date: date | None = Field(default_factory=date.today)
    enabled: bool = True

    @field_validator("name", "category")
    @classmethod
    def clean_text(cls, value: str) -> str:
        return value.strip()

    @model_validator(mode="after")
    def validate_period(self):
        if self.frequency == "yearly" and self.month_of_year is None:
            raise ValueError("请选择每年发生月份")
        if self.frequency == "monthly":
            self.month_of_year = None
        return self


class RecurringExpenseCreate(RecurringExpenseBase):
    pass


class RecurringExpenseUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=80)
    amount: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    category: str | None = Field(default=None, min_length=1, max_length=60)
    frequency: Literal["monthly", "yearly"] | None = None
    day_of_month: int | None = Field(default=None, ge=1, le=31)
    month_of_year: int | None = Field(default=None, ge=1, le=12)
    start_date: date | None = None
    enabled: bool | None = None

    @field_validator("name", "category")
    @classmethod
    def clean_text(cls, value: str | None) -> str | None:
        return value.strip() if value else value


class RecurringExpenseRead(RecurringExpenseBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
