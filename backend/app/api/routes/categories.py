from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.category_preference import CategoryPreference
from app.models.user import User
from app.schemas.category import CategoryPreferenceRead, CategoryPreferenceUpdate

router = APIRouter(prefix="/categories", tags=["categories"])


def empty_preference() -> CategoryPreferenceRead:
    return CategoryPreferenceRead(
        id=None,
        custom_categories=[],
        hidden_category_values=[],
        category_order=[],
        category_colors={},
        updated_at=None,
    )


@router.get("", response_model=CategoryPreferenceRead)
def read_category_preference(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CategoryPreferenceRead:
    preference = db.scalar(select(CategoryPreference).where(CategoryPreference.user_id == current_user.id))
    if preference is None:
        return empty_preference()
    return preference


@router.put("", response_model=CategoryPreferenceRead)
def update_category_preference(
    payload: CategoryPreferenceUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CategoryPreference:
    preference = db.scalar(select(CategoryPreference).where(CategoryPreference.user_id == current_user.id))
    if preference is None:
        preference = CategoryPreference(user_id=current_user.id)

    preference.custom_categories = [item.model_dump() for item in payload.custom_categories]
    preference.hidden_category_values = payload.hidden_category_values
    preference.category_order = payload.category_order
    preference.category_colors = payload.category_colors
    db.add(preference)
    db.commit()
    db.refresh(preference)
    return preference
