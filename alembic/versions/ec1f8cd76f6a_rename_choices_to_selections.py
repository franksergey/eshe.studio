"""Rename choices to selections

Revision ID: ec1f8cd76f6a
Revises: 0bb96a74c5ed
Create Date: 2026-10-24 14:56:58.937033

"""

from typing import TYPE_CHECKING

from alembic import op

if TYPE_CHECKING:
    from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "ec1f8cd76f6a"
down_revision: str | Sequence[str] | None = "0bb96a74c5ed"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.rename_table("user_choices", "user_item_selections")
    op.rename_table("user_item_choices", "user_item_selection_item_snapshots")
    op.rename_table(
        "user_item_choice_groups", "user_item_selection_group_snapshots"
    )

    with op.batch_alter_table(
        "user_item_selection_group_snapshots", schema=None
    ) as batch_op:
        batch_op.alter_column("choice_id", new_column_name="selection_id")
        batch_op.drop_constraint(
            "fk_user_item_choice_groups_choice_id_user_choices",
            type_="foreignkey",
        )
        batch_op.create_foreign_key(
            "fk_user_item_selection_group_snapshots_selection_id",
            "user_item_selections",
            ["selection_id"],
            ["id"],
            ondelete="CASCADE",
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table(
        "user_item_selection_group_snapshots", schema=None
    ) as batch_op:
        batch_op.alter_column("selection_id", new_column_name="choice_id")
        batch_op.drop_constraint(
            "fk_user_item_selection_group_snapshots_selection_id",
            type_="foreignkey",
        )
        batch_op.create_foreign_key(
            "fk_user_item_choice_groups_choice_id_user_choices",
            "user_item_selections",
            ["choice_id"],
            ["id"],
            ondelete="CASCADE",
        )

    op.rename_table("user_item_selection_item_snapshots", "user_item_choices")
    op.rename_table(
        "user_item_selection_group_snapshots", "user_item_choice_groups"
    )
    op.rename_table("user_item_selections", "user_choices")
