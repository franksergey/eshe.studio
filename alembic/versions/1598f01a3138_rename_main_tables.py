"""Rename main tables

Revision ID: 1598f01a3138
Revises: 834af3032825
Create Date: 2026-10-10 23:13:01.682030

"""

from typing import TYPE_CHECKING

from alembic import op

if TYPE_CHECKING:
    from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "1598f01a3138"
down_revision: str | Sequence[str] | None = "834af3032825"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.rename_table("specification_tag", "project_spec_item_tags")
    op.rename_table(
        "specification_item_comments", "project_spec_item_comments"
    )
    op.rename_table("specification_items", "project_spec_items")
    op.rename_table("project_spec_categories", "project_spec_groups")


def downgrade() -> None:
    """Downgrade schema."""
    op.rename_table("project_spec_groups", "project_spec_categories")
    op.rename_table("project_spec_items", "specification_items")
    op.rename_table(
        "project_spec_item_comments", "specification_item_comments"
    )
    op.rename_table("project_spec_item_tags", "specification_tag")
