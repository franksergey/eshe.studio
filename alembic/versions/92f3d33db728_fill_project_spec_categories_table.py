"""Fill project_spec_categories table

Revision ID: 92f3d33db728
Revises: db0daebd93ca
Create Date: 2026-10-09 15:41:51.950622

"""

from typing import TYPE_CHECKING

import sqlalchemy as sa

from alembic import op

if TYPE_CHECKING:
    from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "92f3d33db728"
down_revision: str | Sequence[str] | None = "db0daebd93ca"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

DEFAULT_CATEGORY_NAME = "Automatic"
DEFAULT_CATEGORY_ORDINAL_NO = 0

projects = sa.table("projects", sa.column("id", sa.Integer))
categories = sa.table(
    "project_spec_categories",
    sa.column("id", sa.Integer),
    sa.column("project_id", sa.Integer),
    sa.column("name", sa.String),
    sa.column("ordinal_no", sa.Integer),
)


def upgrade() -> None:
    """Upgrade schema."""
    projects_without_categories = sa.select(
        projects.c.id,
        sa.literal(DEFAULT_CATEGORY_NAME),
        sa.literal(DEFAULT_CATEGORY_ORDINAL_NO),
    ).where(~sa.exists().where(categories.c.project_id == projects.c.id))

    op.execute(
        categories.insert().from_select(
            ["project_id", "name", "ordinal_no"], projects_without_categories
        )
    )


def downgrade() -> None:
    """Downgrade schema."""
