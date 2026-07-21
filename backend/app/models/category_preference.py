from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class CategoryPreference(Base):
    __tablename__ = "category_preferences"
    __table_args__ = (UniqueConstraint("user_id", name="uq_category_preferences_user"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    custom_categories: Mapped[list[dict]] = mapped_column(JSON, nullable=False, default=list)
    hidden_category_values: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    category_order: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    category_colors: Mapped[dict[str, str]] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user = relationship("User", back_populates="category_preference")
