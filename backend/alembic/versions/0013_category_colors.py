from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "0013_category_colors"
down_revision = "0012_category_preferences"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "category_preferences",
        sa.Column("category_colors", sa.JSON(), nullable=True),
    )
    op.execute(sa.text("UPDATE category_preferences SET category_colors = '{}' WHERE category_colors IS NULL"))
    op.alter_column(
        "category_preferences",
        "category_colors",
        existing_type=sa.JSON(),
        nullable=False,
    )


def downgrade() -> None:
    op.drop_column("category_preferences", "category_colors")
