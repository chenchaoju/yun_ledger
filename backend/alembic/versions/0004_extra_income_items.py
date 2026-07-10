"""extra income items

Revision ID: 0004_extra_income_items
Revises: 0003_monthly_incomes
Create Date: 2026-06-01
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0004_extra_income_items"
down_revision = "0003_monthly_incomes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    dialect = op.get_bind().dialect.name

    if dialect == "mysql":
        op.add_column("monthly_incomes", sa.Column("extra_income_items", sa.JSON(), nullable=True))
        op.execute(
            """
            UPDATE monthly_incomes
            SET extra_income_items = JSON_ARRAY(
                JSON_OBJECT('name', '额外收入', 'amount', CAST(extra_income AS DECIMAL(12, 2)))
            )
            WHERE extra_income > 0
            """
        )
        op.execute("UPDATE monthly_incomes SET extra_income_items = JSON_ARRAY() WHERE extra_income_items IS NULL")
        op.alter_column("monthly_incomes", "extra_income_items", existing_type=sa.JSON(), nullable=False)
        return

    op.add_column(
        "monthly_incomes",
        sa.Column("extra_income_items", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
    )
    op.execute(
        """
        UPDATE monthly_incomes
        SET extra_income_items = json_build_array(
            json_build_object('name', '额外收入', 'amount', extra_income::float)
        )
        WHERE extra_income > 0
        """
    )
    op.alter_column("monthly_incomes", "extra_income_items", server_default=None)


def downgrade() -> None:
    dialect = op.get_bind().dialect.name

    if dialect == "mysql":
        op.execute(
            """
            UPDATE monthly_incomes mi
            SET extra_income = COALESCE((
                SELECT SUM(CAST(JSON_UNQUOTE(JSON_EXTRACT(item.value, '$.amount')) AS DECIMAL(12, 2)))
                FROM JSON_TABLE(mi.extra_income_items, '$[*]' COLUMNS(value JSON PATH '$')) AS item
            ), 0)
            WHERE extra_income_items IS NOT NULL
            """
        )
        op.drop_column("monthly_incomes", "extra_income_items")
        return

    op.execute(
        """
        UPDATE monthly_incomes
        SET extra_income = COALESCE((
            SELECT SUM((item->>'amount')::numeric)
            FROM json_array_elements(extra_income_items) AS item
        ), 0)
        WHERE extra_income_items IS NOT NULL
        """
    )
    op.drop_column("monthly_incomes", "extra_income_items")
