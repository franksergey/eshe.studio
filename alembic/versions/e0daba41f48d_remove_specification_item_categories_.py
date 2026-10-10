"""Remove specification_item_categories and specification_rooms

Revision ID: e0daba41f48d
Revises: 19713b8bee7a
Create Date: 2026-10-11 01:05:06.877612

"""

from typing import TYPE_CHECKING

import sqlalchemy as sa

from alembic import op

if TYPE_CHECKING:
    from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "e0daba41f48d"
down_revision: str | Sequence[str] | None = "19713b8bee7a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

groups = sa.table(
    "project_spec_groups",
    sa.column("id", sa.Integer),
    sa.column("project_id", sa.Integer),
    sa.column("group_id", sa.Integer),
    sa.column("name", sa.String(256)),
    sa.column("ordinal_no", sa.Integer),
)
rooms = sa.table(
    "specification_rooms",
    sa.column("id", sa.Integer),
    sa.column("category_id", sa.Integer),
    sa.column("corr_group_id", sa.Integer),
    sa.column("name", sa.String(256)),
    sa.column("ordinal_no", sa.Integer),
)
old_categories = sa.table(
    "specification_item_categories",
    sa.column("id", sa.Integer),
    sa.column("room_id", sa.Integer),
    sa.column("corr_group_id", sa.Integer),
    sa.column("name", sa.String(1024)),
    sa.column("ordinal_no", sa.Integer),
)
items = sa.table(
    "project_spec_items",
    sa.column("id", sa.Integer),
    sa.column("category_id", sa.Integer),
    sa.column("group_id", sa.Integer),
)


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("project_spec_items", schema=None) as batch_op:
        batch_op.drop_constraint(
            batch_op.f(
                "fk_specification_items_category_id_specification_item_categories"
            ),
            type_="foreignkey",
        )
        batch_op.drop_column("category_id")

    op.drop_table("specification_item_categories")
    op.drop_table("specification_rooms")


def groups_to_rooms_migration_statement() -> sa.Insert:
    parent = groups.alias("parent")

    select_stmt = (
        sa.select(
            groups.c.group_id.label("category_id"),
            groups.c.id.label("corr_group_id"),
            groups.c.name.label("name"),
            groups.c.ordinal_no.label("ordinal_no"),
        )
        .select_from(groups.join(parent, groups.c.group_id == parent.c.id))
        .where(parent.c.group_id.is_(None))
    )

    return sa.insert(rooms).from_select(
        ["category_id", "corr_group_id", "name", "ordinal_no"], select_stmt
    )


def groups_to_old_categories_migration_statement() -> sa.Insert:
    select_stmt = sa.select(
        rooms.c.id.label("room_id"),
        groups.c.id.label("corr_group_id"),
        groups.c.name.label("name"),
        groups.c.ordinal_no.label("ordinal_no"),
    ).select_from(
        rooms.join(groups, rooms.c.corr_group_id == groups.c.group_id)
    )

    return sa.insert(old_categories).from_select(
        ["room_id", "corr_group_id", "name", "ordinal_no"], select_stmt
    )


def items_to_old_categories_recursive_statement() -> sa.Update:
    """Map items in level-3 and deeper groups to their level-3 ancestor."""
    anchor = sa.select(
        old_categories.c.corr_group_id.label("group_id"),
        old_categories.c.id.label("category_id"),
    )
    tree = anchor.cte("category_tree", recursive=True)
    child = groups.alias("child")
    tree = tree.union_all(
        sa.select(
            child.c.id.label("group_id"),
            tree.c.category_id.label("category_id"),
        ).select_from(child.join(tree, child.c.group_id == tree.c.group_id))
    )
    return (
        sa.update(items)
        .values(category_id=tree.c.category_id)
        .where(items.c.group_id == tree.c.group_id)
    )


def _items_without_category(group_id_col: object) -> sa.Exists:
    return (
        sa.select(items.c.id)
        .where(items.c.group_id == group_id_col, items.c.category_id.is_(None))
        .exists()
    )


def automatic_rooms_statement() -> sa.Insert:
    """Automatic room for each level-1 group with directly attached items."""
    select_stmt = sa.select(
        groups.c.id.label("category_id"),
        groups.c.id.label("corr_group_id"),
        sa.literal_column("'Automatic'", type_=sa.String).label("name"),
        sa.literal_column("0", type_=sa.Integer).label("ordinal_no"),
    ).where(groups.c.group_id.is_(None), _items_without_category(groups.c.id))

    return sa.insert(rooms).from_select(
        ["category_id", "corr_group_id", "name", "ordinal_no"], select_stmt
    )


def automatic_categories_statement() -> sa.Insert:
    """Automatic category for each level-1/2 group with attached items."""
    select_stmt = (
        sa.select(
            rooms.c.id.label("room_id"),
            groups.c.id.label("corr_group_id"),
            sa.literal_column("'Automatic'", type_=sa.String).label("name"),
            sa.literal_column("0", type_=sa.Integer).label("ordinal_no"),
        )
        .select_from(rooms.join(groups, rooms.c.corr_group_id == groups.c.id))
        .where(_items_without_category(groups.c.id))
    )
    return sa.insert(old_categories).from_select(
        ["room_id", "corr_group_id", "name", "ordinal_no"], select_stmt
    )


def items_to_automatic_categories_statement() -> sa.Update:
    category_id = (
        sa.select(old_categories.c.id)
        .where(old_categories.c.corr_group_id == items.c.group_id)
        .scalar_subquery()
    )
    return (
        sa.update(items)
        .where(items.c.category_id.is_(None))
        .values(category_id=category_id)
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.create_table(
        "specification_rooms",
        sa.Column(
            "id",
            sa.INTEGER(),
            sa.Identity(
                always=True,
                start=1,
                increment=1,
                minvalue=1,
                maxvalue=2147483647,
                cycle=False,
                cache=1,
            ),
            autoincrement=True,
            nullable=False,
        ),
        sa.Column(
            "name", sa.VARCHAR(length=256), autoincrement=False, nullable=False
        ),
        sa.Column(
            "ordinal_no", sa.INTEGER(), autoincrement=False, nullable=False
        ),
        sa.Column(
            "category_id", sa.INTEGER(), autoincrement=False, nullable=False
        ),
        sa.Column(
            "corr_group_id", sa.INTEGER(), autoincrement=False, nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["category_id"],
            ["project_spec_groups.id"],
            name=op.f(
                "fk_specification_rooms_category_id_project_spec_categories"
            ),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["corr_group_id"],
            ["project_spec_groups.id"],
            name=op.f("fk_specification_rooms_corr_group_id"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_specification_rooms")),
    )

    op.create_table(
        "specification_item_categories",
        sa.Column(
            "id",
            sa.INTEGER(),
            sa.Identity(
                always=True,
                start=1,
                increment=1,
                minvalue=1,
                maxvalue=2147483647,
                cycle=False,
                cache=1,
            ),
            autoincrement=True,
            nullable=False,
        ),
        sa.Column(
            "name",
            sa.VARCHAR(length=1024),
            autoincrement=False,
            nullable=False,
        ),
        sa.Column(
            "ordinal_no", sa.INTEGER(), autoincrement=False, nullable=False
        ),
        sa.Column(
            "room_id", sa.INTEGER(), autoincrement=False, nullable=False
        ),
        sa.Column(
            "corr_group_id", sa.INTEGER(), autoincrement=False, nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["room_id"],
            ["specification_rooms.id"],
            name=op.f(
                "fk_specification_items_categories_room_id_specification_rooms"
            ),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["corr_group_id"],
            ["project_spec_groups.id"],
            name=op.f("fk_specification_items_categories_corr_group_id"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "id", name=op.f("pk_specification_items_categories")
        ),
    )

    op.execute(groups_to_rooms_migration_statement())
    op.execute(groups_to_old_categories_migration_statement())

    with op.batch_alter_table("project_spec_items", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "category_id", sa.INTEGER(), autoincrement=False, nullable=True
            )
        )
        batch_op.create_foreign_key(
            batch_op.f(
                "fk_specification_items_category_id_specification_item_categories"
            ),
            "specification_item_categories",
            ["category_id"],
            ["id"],
            ondelete="CASCADE",
        )

    op.execute(items_to_old_categories_recursive_statement())

    op.execute(automatic_rooms_statement())
    op.execute(automatic_categories_statement())
    op.execute(items_to_automatic_categories_statement())

    with op.batch_alter_table("specification_rooms", schema=None) as batch_op:
        batch_op.drop_constraint(
            "fk_specification_rooms_corr_group_id", type_="foreignkey"
        )
        batch_op.drop_column("corr_group_id")

    with op.batch_alter_table(
        "specification_item_categories", schema=None
    ) as batch_op:
        batch_op.drop_constraint(
            "fk_specification_items_categories_corr_group_id",
            type_="foreignkey",
        )
        batch_op.drop_column("corr_group_id")

    with op.batch_alter_table("project_spec_items", schema=None) as batch_op:
        batch_op.alter_column(
            "category_id", existing_nullable=True, nullable=False
        )
