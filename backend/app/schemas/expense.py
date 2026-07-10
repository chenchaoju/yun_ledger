from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ExpenseBase(BaseModel):
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    category: str = Field(min_length=1, max_length=60)
    note: str | None = Field(default=None, max_length=255)
    spent_at: date

    @field_validator("category")
    @classmethod
    def clean_category(cls, value: str) -> str:
        return value.strip()

    @field_validator("note")
    @classmethod
    def clean_note(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None


class ExpenseCreate(ExpenseBase):
    pass


class ExpenseUpdate(BaseModel):
    amount: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    category: str | None = Field(default=None, min_length=1, max_length=60)
    note: str | None = Field(default=None, max_length=255)
    spent_at: date | None = None

    @field_validator("category")
    @classmethod
    def clean_category(cls, value: str | None) -> str | None:
        return value.strip() if value else value

    @field_validator("note")
    @classmethod
    def clean_note(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None


class ExpenseRead(ExpenseBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ExpenseList(BaseModel):
    items: list[ExpenseRead]
    total: int

