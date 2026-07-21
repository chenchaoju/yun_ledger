from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CategoryItem(BaseModel):
    label: str = Field(min_length=1, max_length=60)
    value: str = Field(min_length=1, max_length=60)
    color: str = Field(default="#64748b", min_length=1, max_length=32)
    icon: str = Field(default="MoreFilled", min_length=1, max_length=80)
    custom: bool = True

    @field_validator("label", "value", "color", "icon")
    @classmethod
    def clean_text(cls, value: str) -> str:
        return value.strip()


class CategoryPreferenceBase(BaseModel):
    custom_categories: list[CategoryItem] = Field(default_factory=list)
    hidden_category_values: list[str] = Field(default_factory=list)
    category_order: list[str] = Field(default_factory=list)
    category_colors: dict[str, str] = Field(default_factory=dict)

    @field_validator("hidden_category_values", "category_order")
    @classmethod
    def clean_values(cls, values: list[str]) -> list[str]:
        result: list[str] = []
        seen: set[str] = set()
        for value in values:
            cleaned = str(value or "").strip()
            if cleaned and cleaned not in seen:
                result.append(cleaned)
                seen.add(cleaned)
        return result

    @field_validator("category_colors")
    @classmethod
    def clean_colors(cls, values: dict[str, str]) -> dict[str, str]:
        result: dict[str, str] = {}
        for key, value in values.items():
            category = str(key or "").strip()
            color = str(value or "").strip()
            if category and color:
                result[category] = color
        return result


class CategoryPreferenceUpdate(CategoryPreferenceBase):
    pass


class CategoryPreferenceRead(CategoryPreferenceBase):
    id: int | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
