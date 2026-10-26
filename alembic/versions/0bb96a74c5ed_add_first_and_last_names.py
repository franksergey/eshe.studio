"""Add first and last names

Revision ID: 0bb96a74c5ed
Revises: 10d5c6c051f1
Create Date: 2026-10-26 10:50:55.308353

"""

from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy import update

from alembic import op

if TYPE_CHECKING:
    from collections.abc import Sequence


# revision identifiers, used by Alembic.
revision: str = "0bb96a74c5ed"
down_revision: str | Sequence[str] | None = "10d5c6c051f1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

users_table = sa.table(
    "users",
    sa.Column("email", sa.String(length=320)),
    sa.Column("first_name", sa.String(length=64)),
)


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("first_name", sa.String(length=64), nullable=True)
        )
        batch_op.add_column(
            sa.Column("last_name", sa.String(length=64), nullable=True)
        )

    stmt = update(users_table).values(
        first_name=sa.func.substring(users_table.c.email, 1, 64)
    )
    op.execute(stmt)

    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.alter_column(
            "first_name", existing_type=sa.String(length=64), nullable=False
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_column("last_name")
        batch_op.drop_column("first_name")
