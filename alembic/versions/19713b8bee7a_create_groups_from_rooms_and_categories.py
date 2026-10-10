"""Create groups from rooms and categories

Revision ID: 19713b8bee7a
Revises: 1598f01a3138
Create Date: 2026-10-10 23:36:16.049853

"""

from typing import TYPE_CHECKING

import sqlalchemy as sa

from alembic import op

if TYPE_CHECKING:
    from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "19713b8bee7a"
down_revision: str | Sequence[str] | None = "1598f01a3138"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

groups = sa.table(
    "project_spec_groups",
    sa.column("id", sa.Integer),
    sa.column("project_id", sa.Integer),
    sa.column("group_id", sa.Integer),
    sa.column("room_id", sa.Integer),
    sa.column("category_id", sa.Integer),
    sa.column("name", sa.String(256)),
    sa.column("ordinal_no", sa.Integer),
)
rooms = sa.table(
    "specification_rooms",
    sa.column("id", sa.Integer),
    sa.column("category_id", sa.Integer),
    sa.column("name", sa.String(256)),
    sa.column("ordinal_no", sa.Integer),
)
old_categories = sa.table(
    "specification_item_categories",
    sa.column("id", sa.Integer),
    sa.column("room_id", sa.Integer),
    sa.column("name", sa.String(1024)),
    sa.column("ordinal_no", sa.Integer),
)
items = sa.table(
    "project_spec_items",
    sa.column("id", sa.Integer),
    sa.column("category_id", sa.Integer),
    sa.column("group_id", sa.Integer),
)


def rooms_to_groups_migration_statement() -> sa.Insert:
    parent = groups.alias("parent")

    # One row per (room, parent group). The parent group is the group whose
    # category matches the room's category.
    select_stmt = sa.select(
        parent.c.id.label("group_id"),
        parent.c.project_id.label("project_id"),  # same project as the parent
        rooms.c.id.label("room_id"),
        sa.null().label("category_id"),  # left as NULL
        rooms.c.name.label("name"),
        rooms.c.ordinal_no.label("ordinal_no"),
    ).select_from(rooms.join(parent, parent.c.id == rooms.c.category_id))

    return sa.insert(groups).from_select(
        [
            "group_id",
            "project_id",
            "room_id",
            "category_id",
            "name",
            "ordinal_no",
        ],
        select_stmt,
    )


def old_categories_to_groups_migration_statement() -> sa.Insert:
    parent = groups.alias("parent")

    select_stmt = sa.select(
        parent.c.id.label("group_id"),
        parent.c.project_id.label("project_id"),  # same project as the parent
        sa.null().label("room_id"),  # left as NULL
        old_categories.c.id.label("category_id"),
        old_categories.c.name.label("name"),
        old_categories.c.ordinal_no.label("ordinal_no"),
    ).select_from(
        old_categories.join(
            parent, parent.c.room_id == old_categories.c.room_id
        )
    )

    return sa.insert(groups).from_select(
        [
            "group_id",
            "project_id",
            "room_id",
            "category_id",
            "name",
            "ordinal_no",
        ],
        select_stmt,
    )


def connect_items_to_new_groups_statement() -> sa.Update:
    return (
        items.update()
        .values(group_id=groups.c.id)
        .where(groups.c.category_id == items.c.category_id)
    )


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("project_spec_groups", schema=None) as batch_op:
        batch_op.add_column(sa.Column("room_id", sa.Integer(), nullable=True))
        batch_op.add_column(
            sa.Column("category_id", sa.Integer(), nullable=True)
        )
        batch_op.add_column(sa.Column("group_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            batch_op.f("fk_project_spec_groups_room_id_specification_rooms"),
            "specification_rooms",
            ["room_id"],
            ["id"],
            ondelete="CASCADE",
        )
        batch_op.create_foreign_key(
            batch_op.f(
                "fk_project_spec_groups_category_id_specification_item_categorie"
            ),
            "specification_item_categories",
            ["category_id"],
            ["id"],
            ondelete="CASCADE",
        )
        batch_op.create_foreign_key(
            batch_op.f("fk_project_spec_groups_group_id_project_spec_groups"),
            "project_spec_groups",
            ["group_id"],
            ["id"],
            ondelete="CASCADE",
        )

    op.execute(rooms_to_groups_migration_statement())
    op.execute(old_categories_to_groups_migration_statement())

    with op.batch_alter_table("project_spec_items", schema=None) as batch_op:
        batch_op.add_column(sa.Column("group_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            batch_op.f("fk_project_spec_items_group_id_project_spec_groups"),
            "project_spec_groups",
            ["group_id"],
            ["id"],
            ondelete="CASCADE",
        )

    op.execute(connect_items_to_new_groups_statement())

    with op.batch_alter_table("project_spec_items", schema=None) as batch_op:
        batch_op.alter_column(
            "group_id",
            existing_type=sa.Integer,
            existing_nullable=True,
            nullable=False,
        )

    with op.batch_alter_table("project_spec_groups", schema=None) as batch_op:
        batch_op.drop_constraint(
            "fk_project_spec_groups_room_id_specification_rooms",
            type_="foreignkey",
        )
        batch_op.drop_constraint(
            batch_op.f(
                "fk_project_spec_groups_category_id_specification_item_categorie"
            ),
            type_="foreignkey",
        )
        batch_op.drop_column("room_id")
        batch_op.drop_column("category_id")


def downgrade() -> None:
    """Downgrade schema."""
    # Remove any subgroups
    op.execute(sa.delete(groups).where(groups.c.group_id.is_not(None)))

    with op.batch_alter_table("project_spec_groups", schema=None) as batch_op:
        batch_op.drop_constraint(
            "fk_project_spec_groups_category_id_specification_item_categorie",
            type_="foreignkey",
        )
        batch_op.drop_constraint(
            "fk_project_spec_groups_group_id_project_spec_groups",
            type_="foreignkey",
        )
        batch_op.drop_column("category_id")
        batch_op.drop_column("group_id")

    with op.batch_alter_table("project_spec_items", schema=None) as batch_op:
        batch_op.drop_constraint(
            batch_op.f("fk_project_spec_items_group_id_project_spec_groups"),
            type_="foreignkey",
        )
        batch_op.drop_column("group_id")
