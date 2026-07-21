from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "0012_category_preferences"
down_revision = "0011_seed_reset"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "category_preferences",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("custom_categories", sa.JSON(), nullable=False),
        sa.Column("hidden_category_values", sa.JSON(), nullable=False),
        sa.Column("category_order", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", name="uq_category_preferences_user"),
    )
    op.create_index(op.f("ix_category_preferences_id"), "category_preferences", ["id"], unique=False)
    op.create_index(op.f("ix_category_preferences_user_id"), "category_preferences", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_category_preferences_user_id"), table_name="category_preferences")
    op.drop_index(op.f("ix_category_preferences_id"), table_name="category_preferences")
    op.drop_table("category_preferences")
