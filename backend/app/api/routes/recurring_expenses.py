from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.recurring_expense import RecurringExpense
from app.models.user import User
from app.schemas.recurring_expense import RecurringExpenseCreate, RecurringExpenseRead, RecurringExpenseUpdate

router = APIRouter(prefix="/recurring-expenses", tags=["recurring-expenses"])


def get_owned_recurring_expense(item_id: int, user_id: int, db: Session) -> RecurringExpense:
    item = db.scalar(select(RecurringExpense).where(RecurringExpense.id == item_id, RecurringExpense.user_id == user_id))
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="固定支出不存在")
    return item


@router.get("", response_model=list[RecurringExpenseRead])
def list_recurring_expenses(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[RecurringExpense]:
    return list(
        db.scalars(
            select(RecurringExpense)
            .where(RecurringExpense.user_id == current_user.id)
            .order_by(RecurringExpense.enabled.desc(), RecurringExpense.id.desc())
        ).all()
    )


@router.post("", response_model=RecurringExpenseRead, status_code=status.HTTP_201_CREATED)
def create_recurring_expense(
    payload: RecurringExpenseCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RecurringExpense:
    item = RecurringExpense(user_id=current_user.id, **payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.put("/{item_id}", response_model=RecurringExpenseRead)
def update_recurring_expense(
    item_id: int,
    payload: RecurringExpenseUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RecurringExpense:
    item = get_owned_recurring_expense(item_id, current_user.id, db)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    if item.frequency == "monthly":
        item.month_of_year = None
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_recurring_expense(
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    item = get_owned_recurring_expense(item_id, current_user.id, db)
    db.delete(item)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
