"""Connect specification_rooms table to project_spec_categories

Revision ID: c7545ae0b7df
Revises: 92f3d33db728
Create Date: 2026-10-09 16:11:43.730844

"""

from typing import TYPE_CHECKING

import sqlalchemy as sa

from alembic import op

if TYPE_CHECKING:
    from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "c7545ae0b7df"
down_revision: str | Sequence[str] | None = "92f3d33db728"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

categories = sa.table(
    "project_spec_categories",
    sa.column("id", sa.Integer),
    sa.column("project_id", sa.Integer),
)
rooms = sa.table(
    "specification_rooms",
    sa.column("id", sa.Integer),
    sa.column("specification_id", sa.Integer),
    sa.column("category_id", sa.Integer),
)


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("specification_rooms", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("category_id", sa.Integer(), nullable=True)
        )
        batch_op.create_foreign_key(
            batch_op.f(
                "fk_specification_rooms_category_id_project_spec_categories"
            ),
            "project_spec_categories",
            ["category_id"],
            ["id"],
            ondelete="CASCADE",
        )

    op.execute(
        rooms.update()
        .values(category_id=categories.c.id)
        .where(categories.c.project_id == rooms.c.specification_id)
    )

    with op.batch_alter_table("specification_rooms", schema=None) as batch_op:
        batch_op.alter_column(
            "category_id",
            existing_type=sa.Integer(),
            existing_nullable=True,
            nullable=False,
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("specification_rooms", schema=None) as batch_op:
        batch_op.drop_constraint(
            batch_op.f(
                "fk_specification_rooms_category_id_project_spec_categories"
            ),
            type_="foreignkey",
        )
        batch_op.drop_column("category_id")
