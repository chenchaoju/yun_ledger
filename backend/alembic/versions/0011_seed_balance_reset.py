from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "0011_seed_reset"
down_revision = "0010_balance_reset"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            UPDATE users
            SET opening_balance_reset_at = CURRENT_TIMESTAMP
            WHERE opening_balance_reset_at IS NULL
              AND opening_balance_amount <> 0
            """
        )
    )


def downgrade() -> None:
    pass
