"""Change approved to status column

Revision ID: a34b3621c90c
Revises: 6c9bee69fc9e
Create Date: 2026-10-29 00:52:21.704264

"""

from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy import or_, update

from alembic import op

if TYPE_CHECKING:
    from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "a34b3621c90c"
down_revision: str | Sequence[str] | None = "6c9bee69fc9e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

ITEM_STATUS_ENUM = sa.Enum("approved", "paid", name="item_status_enum")
items_table = sa.table(
    "project_spec_items",
    sa.column("status", ITEM_STATUS_ENUM),
    sa.column("approved", sa.Boolean),
)


def upgrade() -> None:
    """Upgrade schema."""
    ITEM_STATUS_ENUM.create(bind=op.get_bind())

    with op.batch_alter_table("project_spec_items", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("status", ITEM_STATUS_ENUM, nullable=True)
        )

    stmt = (
        update(items_table)
        .values(status="approved")
        .where(items_table.c.approved.is_(True))
    )
    op.execute(stmt)

    with op.batch_alter_table("project_spec_items", schema=None) as batch_op:
        batch_op.drop_column("approved")


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("project_spec_items", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "approved",
                sa.Boolean(),
                nullable=False,
                server_default=sa.sql.false(),
            )
        )

    stmt = (
        update(items_table)
        .values(approved=True)
        .where(
            or_(
                items_table.c.status == "approved",
                items_table.c.status == "paid",
            )
        )
    )
    op.execute(stmt)

    with op.batch_alter_table("project_spec_items", schema=None) as batch_op:
        batch_op.alter_column(
            "approved",
            existing_type=sa.Boolean,
            existing_nullable=False,
            server_default=None,
        )
        batch_op.drop_column("status")

    ITEM_STATUS_ENUM.drop(bind=op.get_bind())
