"""align existing PostgreSQL users table

Revision ID: 0002_align_postgresql_users
Revises: 0001_initial
Create Date: 2026-05-27
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0002_align_postgresql_users"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def _column_map(table_name: str) -> dict[str, dict]:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return {column["name"]: column for column in inspector.get_columns(table_name)}


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table("users"):
        return

    columns = _column_map("users")

    if "password_hash" not in columns:
        op.add_column("users", sa.Column("password_hash", sa.String(length=255), nullable=True))

    created_at = columns.get("created_at")
    if created_at and not isinstance(created_at["type"], sa.DateTime):
        if "created_at_legacy" not in columns:
            op.alter_column("users", "created_at", new_column_name="created_at_legacy")
        else:
            op.drop_column("users", "created_at")

        op.add_column(
            "users",
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
        )
    elif "created_at" not in columns:
        op.add_column(
            "users",
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
        )


def downgrade() -> None:
    columns = _column_map("users")

    if "password_hash" in columns:
        op.drop_column("users", "password_hash")

    columns = _column_map("users")
    if "created_at_legacy" in columns and "created_at" in columns:
        op.drop_column("users", "created_at")
        op.alter_column("users", "created_at_legacy", new_column_name="created_at")

