from __future__ import annotations

from datetime import date, datetime

from decimal import Decimal

from sqlalchemy import Date, DateTime, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    username: Mapped[str | None] = mapped_column(String(80), nullable=True)
    default_salary_income: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    opening_balance_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    opening_balance_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    opening_balance_reset_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    expenses = relationship("Expense", back_populates="user", cascade="all, delete-orphan")
    monthly_incomes = relationship("MonthlyIncome", back_populates="user", cascade="all, delete-orphan")
    recurring_expenses = relationship("RecurringExpense", back_populates="user", cascade="all, delete-orphan")
    category_preference = relationship(
        "CategoryPreference",
        back_populates="user",
        cascade="all, delete-orphan",
        uselist=False,
    )
