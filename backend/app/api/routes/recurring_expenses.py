from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.recurring_expense import RecurringExpense
from app.models.user import User
from app.schemas.recurring_expense import RecurringExpenseCreate, RecurringExpenseRead, RecurringExpenseUpdate
from app.services.recurring_expenses import materialize_recurring_expenses

router = APIRouter(prefix="/recurring-expenses", tags=["recurring-expenses"])


def get_owned(rule_id: int, user_id: int, db: Session) -> RecurringExpense:
    rule = db.scalar(select(RecurringExpense).where(RecurringExpense.id == rule_id, RecurringExpense.user_id == user_id))
    if rule is None:
        raise HTTPException(status_code=404, detail="固定支出不存在")
    return rule


@router.get("", response_model=list[RecurringExpenseRead])
def list_rules(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    materialize_recurring_expenses(db, current_user.id)
    return list(db.scalars(select(RecurringExpense).where(RecurringExpense.user_id == current_user.id).order_by(RecurringExpense.id.desc())).all())


@router.post("", response_model=RecurringExpenseRead, status_code=status.HTTP_201_CREATED)
def create_rule(payload: RecurringExpenseCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rule = RecurringExpense(user_id=current_user.id, **payload.model_dump())
    db.add(rule); db.commit(); db.refresh(rule)
    materialize_recurring_expenses(db, current_user.id)
    return rule


@router.put("/{rule_id}", response_model=RecurringExpenseRead)
def update_rule(rule_id: int, payload: RecurringExpenseUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rule = get_owned(rule_id, current_user.id, db)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(rule, key, value)
    db.add(rule); db.commit(); db.refresh(rule)
    materialize_recurring_expenses(db, current_user.id)
    return rule


@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_rule(rule_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db.delete(get_owned(rule_id, current_user.id, db)); db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
