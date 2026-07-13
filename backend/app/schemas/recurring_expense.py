from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class RecurringExpenseBase(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    category: str = Field(default="会员订阅", min_length=1, max_length=60)
    frequency: Literal["monthly", "yearly"]
    start_date: date
    is_active: bool = True


class RecurringExpenseCreate(RecurringExpenseBase):
    pass


class RecurringExpenseUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=80)
    amount: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    category: str | None = Field(default=None, min_length=1, max_length=60)
    frequency: Literal["monthly", "yearly"] | None = None
    start_date: date | None = None
    is_active: bool | None = None


class RecurringExpenseRead(RecurringExpenseBase):
    id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)
