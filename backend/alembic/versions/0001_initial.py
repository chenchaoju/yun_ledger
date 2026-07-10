"""initial tables

Revision ID: 0001_initial
Revises:
Create Date: 2026-05-25
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def _create_index_if_missing(index_name: str, table_name: str, columns: list[str], unique: bool = False) -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    exists = any(index["name"] == index_name for index in inspector.get_indexes(table_name))
    if not exists:
        op.create_index(index_name, table_name, columns, unique=unique)


def upgrade() -> None:
    dialect = op.get_bind().dialect.name

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        if_not_exists=True,
    )
    if dialect == "mysql":
        _create_index_if_missing(op.f("ix_users_email"), "users", ["email"], unique=True)
    else:
        op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True, if_not_exists=True)

    op.create_table(
        "expenses",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("category", sa.String(length=60), nullable=False),
        sa.Column("note", sa.String(length=255), nullable=True),
        sa.Column("spent_at", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        if_not_exists=True,
    )
    if dialect == "mysql":
        _create_index_if_missing(op.f("ix_expenses_spent_at"), "expenses", ["spent_at"])
        _create_index_if_missing(op.f("ix_expenses_user_id"), "expenses", ["user_id"])
    else:
        op.create_index(op.f("ix_expenses_spent_at"), "expenses", ["spent_at"], unique=False, if_not_exists=True)
        op.create_index(op.f("ix_expenses_user_id"), "expenses", ["user_id"], unique=False, if_not_exists=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_expenses_user_id"), table_name="expenses")
    op.drop_index(op.f("ix_expenses_spent_at"), table_name="expenses")
    op.drop_table("expenses")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
