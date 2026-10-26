"""Rewire selections tables

Revision ID: 9eefeabd2e80
Revises: ec1f8cd76f6a
Create Date: 2026-10-26 01:37:04.914814

"""

from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy import DateTime

from alembic import op

if TYPE_CHECKING:
    from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "9eefeabd2e80"
down_revision: str | Sequence[str] | None = "ec1f8cd76f6a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table(
        "user_item_selection_item_snapshots", schema=None
    ) as batch_op:
        batch_op.add_column(
            sa.Column("selection_id", sa.Integer(), nullable=False)
        )
        batch_op.alter_column(
            "item_id", existing_type=sa.INTEGER(), nullable=False
        )
        batch_op.drop_constraint(
            batch_op.f("fk_user_item_choices_item_id_project_spec_items"),
            type_="foreignkey",
        )
        batch_op.drop_constraint(
            batch_op.f(
                "fk_user_item_choices_group_id_user_item_choice_groups"
            ),
            type_="foreignkey",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_user_item_selection_item_snapshots_item_id"),
            "project_spec_items",
            ["item_id"],
            ["id"],
            ondelete="CASCADE",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_user_item_selection_item_snapshots_selection_id"),
            "user_item_selections",
            ["selection_id"],
            ["id"],
        )

    with op.batch_alter_table("user_item_selections", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("project_id", sa.Integer(), nullable=False)
        )
        batch_op.add_column(
            sa.Column(
                "updated_at",
                DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            )
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_user_item_selections_project_id"),
            "projects",
            ["project_id"],
            ["id"],
            ondelete="CASCADE",
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("user_item_selections", schema=None) as batch_op:
        batch_op.drop_constraint(
            batch_op.f("fk_user_item_selections_project_id"),
            type_="foreignkey",
        )
        batch_op.drop_column("updated_at")
        batch_op.drop_column("project_id")

    with op.batch_alter_table(
        "user_item_selection_item_snapshots", schema=None
    ) as batch_op:
        batch_op.drop_constraint(
            batch_op.f("fk_user_item_selection_item_snapshots_selection_id"),
            type_="foreignkey",
        )
        batch_op.drop_constraint(
            batch_op.f("fk_user_item_selection_item_snapshots_item_id"),
            type_="foreignkey",
        )
        batch_op.create_foreign_key(
            batch_op.f(
                "fk_user_item_choices_group_id_user_item_choice_groups"
            ),
            "user_item_selection_group_snapshots",
            ["group_id"],
            ["id"],
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_user_item_choices_item_id_project_spec_items"),
            "project_spec_items",
            ["item_id"],
            ["id"],
            ondelete="SET NULL",
        )
        batch_op.alter_column(
            "item_id", existing_type=sa.INTEGER(), nullable=True
        )
        batch_op.drop_column("selection_id")
