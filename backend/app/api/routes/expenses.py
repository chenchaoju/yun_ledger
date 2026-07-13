from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.expense import Expense
from app.models.user import User
from app.schemas.expense import ExpenseCreate, ExpenseList, ExpenseRead, ExpenseUpdate
from app.services.recurring_expenses import materialize_recurring_expenses

router = APIRouter(prefix="/expenses", tags=["expenses"])


def get_owned_expense(expense_id: int, user_id: int, db: Session) -> Expense:
    expense = db.scalar(select(Expense).where(Expense.id == expense_id, Expense.user_id == user_id))
    if expense is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="记录不存在")
    return expense


@router.get("", response_model=ExpenseList)
def list_expenses(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    category: str | None = Query(default=None),
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> ExpenseList:
    materialize_recurring_expenses(db, current_user.id)
    filters = [Expense.user_id == current_user.id]

    if start_date:
        filters.append(Expense.spent_at >= start_date)
    if end_date:
        filters.append(Expense.spent_at <= end_date)
    if category:
        filters.append(Expense.category == category.strip())

    total = db.scalar(select(func.count()).select_from(Expense).where(*filters)) or 0
    items = db.scalars(
        select(Expense)
        .where(*filters)
        .order_by(Expense.spent_at.desc(), Expense.id.desc())
        .offset(offset)
        .limit(limit)
    ).all()

    return ExpenseList(items=list(items), total=total)


@router.post("", response_model=ExpenseRead, status_code=status.HTTP_201_CREATED)
def create_expense(
    payload: ExpenseCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Expense:
    expense = Expense(user_id=current_user.id, **payload.model_dump())
    db.add(expense)
    db.commit()
    db.refresh(expense)
    return expense


@router.get("/{expense_id}", response_model=ExpenseRead)
def read_expense(
    expense_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Expense:
    return get_owned_expense(expense_id, current_user.id, db)


@router.put("/{expense_id}", response_model=ExpenseRead)
def update_expense(
    expense_id: int,
    payload: ExpenseUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Expense:
    expense = get_owned_expense(expense_id, current_user.id, db)

    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(expense, key, value)

    db.add(expense)
    db.commit()
    db.refresh(expense)
    return expense


@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense(
    expense_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    expense = get_owned_expense(expense_id, current_user.id, db)
    db.delete(expense)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
