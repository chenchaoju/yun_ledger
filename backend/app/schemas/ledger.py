from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator


class LedgerRecord(BaseModel):
    id: str
    record_type: str
    amount: float
    category: str
    note: str | None = None
    record_date: date
    source_id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class LedgerRecordList(BaseModel):
    items: list[LedgerRecord]
    total: int


class LedgerRecordUpdate(BaseModel):
    amount: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    category: str | None = Field(default=None, min_length=1, max_length=60)
    note: str | None = Field(default=None, max_length=255)
    record_date: date | None = None

    @field_validator("category", "note")
    @classmethod
    def clean_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None
