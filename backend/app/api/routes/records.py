from __future__ import annotations

from calendar import monthrange
from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import extract, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.expense import Expense
from app.models.monthly_income import MonthlyIncome
from app.models.recurring_expense import RecurringExpense
from app.models.user import User
from app.schemas.ledger import LedgerRecord, LedgerRecordList, LedgerRecordUpdate
from app.services.income_items import extra_income_total, normalize_extra_income_items
from app.services.recurring_expenses import recurring_occurrences_between

router = APIRouter(prefix="/records", tags=["records"])


def to_float(value) -> float:
    return round(float(value or 0), 2)


def month_start(year: int, month: int) -> date:
    return date(year, month, 1)


def month_end(year: int, month: int) -> date:
    return date(year, month, monthrange(year, month)[1])


def iter_months(start_date: date, end_date: date):
    year = start_date.year
    month = start_date.month
    while (year, month) <= (end_date.year, end_date.month):
        yield year, month
        month += 1
        if month > 12:
            year += 1
            month = 1


def get_or_create_income(user: User, year: int, month: int, db: Session) -> MonthlyIncome:
    income = db.scalar(
        select(MonthlyIncome).where(
            MonthlyIncome.user_id == user.id,
            MonthlyIncome.year == year,
            MonthlyIncome.month == month,
        )
    )
    if income is not None:
        return income

    income = MonthlyIncome(
        user_id=user.id,
        year=year,
        month=month,
        salary_income=user.default_salary_income or 0,
        extra_income=0,
        extra_income_items=[],
    )
    db.add(income)
    db.flush()
    return income


def parse_record_id(record_id: str) -> tuple[str, list[str]]:
    parts = record_id.split("-")
    if record_id.startswith("expense-") and len(parts) == 2:
        return "expense", [parts[1]]
    if record_id.startswith("salary-") and len(parts) == 3:
        return "salary", [parts[1], parts[2]]
    if record_id.startswith("extra-income-") and len(parts) == 4:
        return "extra_income", [parts[2], parts[3]]
    if record_id.startswith("recurring-") and len(parts) >= 3:
        item_id = parts[1]
        occurrence_date = "-".join(parts[2:])
        return "recurring_expense", [item_id, occurrence_date]
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="明细类型不支持")


def get_owned_expense(expense_id: int, user_id: int, db: Session) -> Expense:
    expense = db.scalar(select(Expense).where(Expense.id == expense_id, Expense.user_id == user_id))
    if expense is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="明细不存在")
    return expense


def get_owned_recurring(item_id: int, user_id: int, db: Session) -> RecurringExpense:
    item = db.scalar(select(RecurringExpense).where(RecurringExpense.id == item_id, RecurringExpense.user_id == user_id))
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="固定支出不存在")
    return item


@router.get("", response_model=LedgerRecordList)
def list_records(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    category: str | None = Query(default=None),
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> LedgerRecordList:
    category_value = category.strip() if category else None
    records: list[LedgerRecord] = []
    today = date.today()
    range_start = start_date or date(today.year, 1, 1)
    range_end = min(end_date or today, today)

    expense_filters = [Expense.user_id == current_user.id]
    if start_date:
        expense_filters.append(Expense.spent_at >= start_date)
    if end_date:
        expense_filters.append(Expense.spent_at <= end_date)
    if category_value:
        expense_filters.append(Expense.category == category_value)

    expenses = db.scalars(select(Expense).where(*expense_filters)).all()
    records.extend(
        LedgerRecord(
            id=f"expense-{expense.id}",
            record_type="expense",
            source_id=expense.id,
            amount=to_float(expense.amount),
            category=expense.category,
            note=expense.note,
            record_date=expense.spent_at,
            created_at=expense.created_at,
            updated_at=expense.updated_at,
        )
        for expense in expenses
    )

    recurring_items = list(db.scalars(select(RecurringExpense).where(RecurringExpense.user_id == current_user.id)).all())
    recurring_occurrences = recurring_occurrences_between(recurring_items, range_start, range_end) if range_start <= today else []
    active_months: set[tuple[int, int]] = {
        (expense.spent_at.year, expense.spent_at.month)
        for expense in db.scalars(
            select(Expense).where(
                Expense.user_id == current_user.id,
                Expense.spent_at >= range_start,
                Expense.spent_at <= range_end,
            )
        ).all()
    }
    for occurrence in recurring_occurrences:
        active_months.add((occurrence.record_date.year, occurrence.record_date.month))
        if category_value and occurrence.category != category_value:
            continue
        records.append(
            LedgerRecord(
                id=occurrence.id,
                record_type="recurring_expense",
                source_id=occurrence.source_id,
                amount=to_float(occurrence.amount),
                category=occurrence.category,
                note=occurrence.name,
                record_date=occurrence.record_date,
                created_at=occurrence.created_at,
                updated_at=occurrence.updated_at,
            )
        )

    income_months = list(iter_months(range_start, range_end)) if range_start <= range_end else []
    income_rows = db.scalars(
        select(MonthlyIncome).where(
            MonthlyIncome.user_id == current_user.id,
            MonthlyIncome.year >= range_start.year,
            MonthlyIncome.year <= range_end.year,
        )
    ).all()
    income_map = {
        (income.year, income.month): income
        for income in income_rows
        if month_end(income.year, income.month) >= range_start and month_start(income.year, income.month) <= range_end
    }
    extra_income_records: list[LedgerRecord] = []
    for (year, month), income in income_map.items():
        items = normalize_extra_income_items(income.extra_income_items, income.extra_income)
        for index, item in enumerate(items):
            record_date_text = item.get("occurred_at")
            record_date = date.fromisoformat(record_date_text) if record_date_text else month_start(year, month)
            if record_date < range_start or record_date > range_end:
                continue
            active_months.add((record_date.year, record_date.month))
            extra_income_records.append(
                LedgerRecord(
                    id=f"extra-income-{income.id}-{index}",
                    record_type="extra_income",
                    source_id=income.id,
                    amount=to_float(item.get("amount")),
                    category="额外收入",
                    note=item.get("name") or "额外收入",
                    record_date=record_date,
                    created_at=income.created_at,
                    updated_at=income.updated_at,
                )
            )

    if not category_value or category_value == "工资收入":
        for year, month in income_months:
            key = (year, month)
            is_current_month = key == (today.year, today.month)
            if not is_current_month and key not in active_months:
                continue
            income = income_map.get((year, month))
            salary_income = to_float(income.salary_income) if income else to_float(current_user.default_salary_income)
            if salary_income <= 0:
                continue
            record_date = month_start(year, month)
            if record_date < range_start or record_date > range_end:
                continue
            records.append(
                LedgerRecord(
                    id=f"salary-{year}-{month}",
                    record_type="salary_income",
                    source_id=income.id if income else None,
                    amount=salary_income,
                    category="工资收入",
                    note="工资收入",
                    record_date=record_date,
                    created_at=income.created_at if income else current_user.created_at,
                    updated_at=income.updated_at if income else None,
                )
            )

    if not category_value or category_value == "额外收入":
        records.extend(extra_income_records)

    records.sort(
        key=lambda item: (
            item.record_date,
            (item.updated_at or item.created_at).isoformat() if item.updated_at or item.created_at else "",
            item.id,
        ),
        reverse=True,
    )
    total = len(records)
    return LedgerRecordList(items=records[offset : offset + limit], total=total)


@router.put("/{record_id}", response_model=LedgerRecord)
def update_record(
    record_id: str,
    payload: LedgerRecordUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> LedgerRecord:
    record_type, values = parse_record_id(record_id)
    data = payload.model_dump(exclude_unset=True)

    if record_type == "expense":
        expense = get_owned_expense(int(values[0]), current_user.id, db)
        if "amount" in data and data["amount"] is not None:
            if data["amount"] <= 0:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="金额必须大于 0")
            expense.amount = data["amount"]
        if "category" in data and data["category"]:
            expense.category = data["category"]
        if "note" in data:
            expense.note = data["note"]
        if "record_date" in data and data["record_date"]:
            expense.spent_at = data["record_date"]
        db.add(expense)
        db.commit()
        db.refresh(expense)
        return LedgerRecord(
            id=f"expense-{expense.id}",
            record_type="expense",
            source_id=expense.id,
            amount=to_float(expense.amount),
            category=expense.category,
            note=expense.note,
            record_date=expense.spent_at,
            created_at=expense.created_at,
            updated_at=expense.updated_at,
        )

    if record_type == "salary":
        year = int(values[0])
        month = int(values[1])
        income = get_or_create_income(current_user, year, month, db)
        if "amount" in data and data["amount"] is not None:
            income.salary_income = data["amount"]
        db.add(income)
        db.commit()
        db.refresh(income)
        return LedgerRecord(
            id=f"salary-{year}-{month}",
            record_type="salary_income",
            source_id=income.id,
            amount=to_float(income.salary_income),
            category="工资收入",
            note="工资收入",
            record_date=month_start(year, month),
            created_at=income.created_at,
            updated_at=income.updated_at,
        )

    if record_type == "extra_income":
        income_id = int(values[0])
        item_index = int(values[1])
        income = db.scalar(select(MonthlyIncome).where(MonthlyIncome.id == income_id, MonthlyIncome.user_id == current_user.id))
        if income is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="收入明细不存在")
        items = normalize_extra_income_items(income.extra_income_items, income.extra_income)
        if item_index < 0 or item_index >= len(items):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="收入明细不存在")
        item = dict(items[item_index])
        if "amount" in data and data["amount"] is not None:
            if data["amount"] <= 0:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="金额必须大于 0")
            item["amount"] = to_float(data["amount"])
        if "note" in data and data["note"]:
            item["name"] = data["note"]
        if "record_date" in data and data["record_date"]:
            item["occurred_at"] = data["record_date"].isoformat()
        items[item_index] = item
        income.extra_income_items = items
        income.extra_income = extra_income_total(items)
        db.add(income)
        db.commit()
        db.refresh(income)
        record_date = date.fromisoformat(item["occurred_at"]) if item.get("occurred_at") else month_start(income.year, income.month)
        return LedgerRecord(
            id=f"extra-income-{income.id}-{item_index}",
            record_type="extra_income",
            source_id=income.id,
            amount=to_float(item["amount"]),
            category="额外收入",
            note=item["name"],
            record_date=record_date,
            created_at=income.created_at,
            updated_at=income.updated_at,
        )

    item = get_owned_recurring(int(values[0]), current_user.id, db)
    occurrence_date = date.fromisoformat(values[1])
    if "amount" in data and data["amount"] is not None:
        if data["amount"] <= 0:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="金额必须大于 0")
        item.amount = data["amount"]
    if "category" in data and data["category"]:
        item.category = data["category"]
    if "note" in data and data["note"]:
        item.name = data["note"]
    if "record_date" in data and data["record_date"]:
        occurrence_date = data["record_date"]
        item.day_of_month = occurrence_date.day
        if item.frequency == "yearly":
            item.month_of_year = occurrence_date.month
    db.add(item)
    db.commit()
    db.refresh(item)
    return LedgerRecord(
        id=f"recurring-{item.id}-{occurrence_date.isoformat()}",
        record_type="recurring_expense",
        source_id=item.id,
        amount=to_float(item.amount),
        category=item.category,
        note=item.name,
        record_date=occurrence_date,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


@router.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_record(
    record_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    record_type, values = parse_record_id(record_id)

    if record_type == "expense":
        expense = get_owned_expense(int(values[0]), current_user.id, db)
        db.delete(expense)
    elif record_type == "extra_income":
        income_id = int(values[0])
        item_index = int(values[1])
        income = db.scalar(select(MonthlyIncome).where(MonthlyIncome.id == income_id, MonthlyIncome.user_id == current_user.id))
        if income is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="收入明细不存在")
        items = normalize_extra_income_items(income.extra_income_items, income.extra_income)
        if item_index < 0 or item_index >= len(items):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="收入明细不存在")
        items.pop(item_index)
        income.extra_income_items = items
        income.extra_income = extra_income_total(items)
        db.add(income)
    elif record_type == "salary":
        year = int(values[0])
        month = int(values[1])
        income = get_or_create_income(current_user, year, month, db)
        income.salary_income = Decimal("0")
        db.add(income)
    else:
        item = get_owned_recurring(int(values[0]), current_user.id, db)
        item.enabled = False
        db.add(item)

    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
