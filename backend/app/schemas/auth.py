from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class UserCreate(BaseModel):
    username: str | None = Field(default=None, min_length=1, max_length=80)
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=1, max_length=128)


class UserUpdate(BaseModel):
    username: str | None = Field(default=None, min_length=1, max_length=80)
    default_salary_income: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    opening_balance_date: date | None = None
    opening_balance_amount: Decimal | None = Field(default=None, max_digits=12, decimal_places=2)


class UserRead(BaseModel):
    id: int
    email: str
    username: str | None = None
    default_salary_income: float = 0
    opening_balance_date: date | None = None
    opening_balance_amount: float = 0
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead
