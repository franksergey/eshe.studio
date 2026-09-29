"""Use identity for primary_key fields

Revision ID: 07c15aaf8b6b
Revises: 2edb1ebad207
Create Date: 2026-09-27 21:03:06.385228

"""

from typing import TYPE_CHECKING

import sqlalchemy as sa

from alembic import op

if TYPE_CHECKING:
    from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "07c15aaf8b6b"
down_revision: str | Sequence[str] | None = "2edb1ebad207"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


TABLES = [
    "specification_items",
    "specification_items_categories",
    "specification_rooms",
    "specifications",
]


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()

    if bind.dialect.name != "postgresql":
        # SQLite (and other dialects without a native IDENTITY construct)
        # already treat an INTEGER PRIMARY KEY as an autoincrementing
        # identity column, and Alembic's batch/table-recreation path can't
        # render sa.Identity() as a server_default (it isn't a valid
        # Column.server_default value outside of Postgres' special-cased
        # ALTER ... ADD GENERATED AS IDENTITY handling). Nothing to do here.
        return

    for table_name in TABLES:
        op.alter_column(
            table_name,
            "id",
            existing_type=sa.INTEGER(),
            server_default=None,
            existing_nullable=False,
        )
        sa.Sequence(f"{table_name}_id_seq").drop(
            op.get_bind(), checkfirst=True
        )
        op.alter_column(
            table_name,
            "id",
            existing_type=sa.INTEGER(),
            existing_server_default=None,
            server_default=sa.Identity(always=True),
            existing_nullable=False,
        )


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()

    if bind.dialect.name != "postgresql":
        return

    for table_name in TABLES:
        op.alter_column(
            table_name,
            "id",
            existing_type=sa.INTEGER(),
            existing_server_default=sa.Identity(always=True),
            server_default=None,
            existing_nullable=False,
        )
        seq = sa.Sequence(f"{table_name}_id_seq")
        seq.create(op.get_bind(), checkfirst=True)
        op.alter_column(
            table_name,
            "id",
            existing_type=sa.INTEGER(),
            existing_server_default=None,
            server_default=seq.next_value(),
            existing_nullable=False,
        )
