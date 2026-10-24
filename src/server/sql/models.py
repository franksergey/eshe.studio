import uuid
from decimal import Decimal
from typing import ClassVar

from fastapi_users.db import SQLAlchemyBaseUserTableUUID
from fastapi_users_db_sqlalchemy.generics import GUID
from sqlalchemy import (
    JSON,
    CheckConstraint,
    Enum,
    ForeignKey,
    Identity,
    MetaData,
    Numeric,
    SmallInteger,
    String,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    declarative_mixin,
    mapped_column,
    relationship,
)

from server.config import settings
from server.domain.files.schemas import ContentType
from server.domain.projects.schemas import CurrencyCode
from server.sql.mixins import CreatedAtMixin, TimestampMixin


class Base(DeclarativeBase):
    metadata: ClassVar[MetaData] = MetaData(
        naming_convention={
            "ix": "ix_%(table_name)s_%(column_0_label)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_%(constraint_name)s",
            "fk": ("fk_%(table_name)s_%(column_0_name)s"),
            "pk": "pk_%(table_name)s",
        }
    )


IDENTITY = (
    Identity(always=True) if settings.db.DIALECT == "postgresql" else None
)

JsonType = JSON().with_variant(JSONB, "postgresql")

# ===============
# Projects Domain
# ===============


class SpecificationTagDB(Base):
    __tablename__ = "project_spec_item_tags"

    item_id: Mapped[int] = mapped_column(
        ForeignKey("project_spec_items.id", ondelete="CASCADE"),
        primary_key=True,
    )
    ordinal_no: Mapped[int] = mapped_column(primary_key=True)

    tag: Mapped[str] = mapped_column(String(255))

    # Relations
    item: Mapped[ItemDB] = relationship(back_populates="tags")


class CommentDB(Base, CreatedAtMixin):
    __tablename__ = "project_spec_item_comments"

    id: Mapped[int] = mapped_column(IDENTITY, primary_key=True)
    item_id: Mapped[int] = mapped_column(
        ForeignKey("project_spec_items.id", ondelete="CASCADE")
    )

    text: Mapped[str] = mapped_column(String(4096))
    author_name: Mapped[str] = mapped_column(String(128))

    # Relations
    item: Mapped[ItemDB] = relationship(back_populates="comments")


PYDANTIC_MAX_URL_LENGTH = 2083
CURRENCY_CODE_ENUM = Enum(CurrencyCode, name="currency_code_enum")


@declarative_mixin
class ItemTableBase:
    name: Mapped[str] = mapped_column(String(1024))
    count: Mapped[int] = mapped_column(SmallInteger)
    approved: Mapped[bool] = mapped_column(default=False)

    link: Mapped[str | None] = mapped_column(String(PYDANTIC_MAX_URL_LENGTH))

    price: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=12, scale=2)
    )
    price_currency: Mapped[CurrencyCode | None] = mapped_column(
        CURRENCY_CODE_ENUM
    )


class ItemDB(ItemTableBase, Base):
    """Вариант предмета в таблице комплектации."""

    __tablename__ = "project_spec_items"

    id: Mapped[int] = mapped_column(IDENTITY, primary_key=True)
    group_id: Mapped[int] = mapped_column(
        ForeignKey("project_spec_groups.id", ondelete="CASCADE")
    )
    image_id: Mapped[int | None] = mapped_column(ForeignKey("images.id"))
    ordinal_no: Mapped[int] = mapped_column()

    # Relations
    tags: Mapped[list[SpecificationTagDB]] = relationship(
        back_populates="item",
        cascade="all, delete, delete-orphan",
        passive_deletes=True,
        lazy="selectin",
        order_by=SpecificationTagDB.ordinal_no,
    )
    comments: Mapped[list[CommentDB]] = relationship(
        back_populates="item",
        cascade="all, delete, delete-orphan",
        passive_deletes=True,
    )
    group: Mapped[GroupDB] = relationship(back_populates="items")
    image: Mapped[ImageDB | None] = relationship(lazy="joined")

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "(price IS NULL AND price_currency IS NULL) "
            "OR NOT(price IS NULL OR price_currency IS NULL)",
            name="ux_c_email_or_phone_required",
        ),
    )


class GroupDB(Base):
    """Категория карточек в таблице комплектации."""

    __tablename__ = "project_spec_groups"

    id: Mapped[int] = mapped_column(IDENTITY, primary_key=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE")
    )
    group_id: Mapped[int | None] = mapped_column(
        ForeignKey("project_spec_groups.id", ondelete="CASCADE")
    )

    name: Mapped[str] = mapped_column(String(256))
    ordinal_no: Mapped[int] = mapped_column()

    # Relations
    items: Mapped[list[ItemDB]] = relationship(
        back_populates="group",
        cascade="all, delete, delete-orphan",
        passive_deletes=True,
        lazy="selectin",
        order_by=ItemDB.ordinal_no,
    )
    subgroups: Mapped[list[GroupDB]] = relationship(
        back_populates="parent_group",
        cascade="all, delete, delete-orphan",
        passive_deletes=True,
        lazy="selectin",
        join_depth=10,
        order_by="GroupDB.ordinal_no",
    )
    parent_group: Mapped[GroupDB | None] = relationship(
        back_populates="subgroups", remote_side="GroupDB.id"
    )
    project: Mapped[ProjectDB] = relationship(
        foreign_keys=[project_id], back_populates="categories"
    )


class ProjectDB(Base):
    """Архитектурный проект."""

    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(IDENTITY, primary_key=True)

    # Or location?
    name: Mapped[str] = mapped_column(String(256))

    # Relations
    categories: Mapped[list[GroupDB]] = relationship(
        primaryjoin=(
            "and_(ProjectDB.id == GroupDB.project_id, "
            "GroupDB.group_id.is_(None))"
        ),
        back_populates="project",
        viewonly=True,
        cascade="all, delete, delete-orphan",
        lazy="selectin",
        order_by=GroupDB.ordinal_no,
    )


# ============
# Users Domain
# ============


class UserDB(SQLAlchemyBaseUserTableUUID, Base):
    __tablename__ = "users"

    # Relations
    choices: Mapped[list[ChoiceDB]] = relationship(
        back_populates="user", order_by="ChoiceDB.created_at"
    )


# ==============
# Choices Domain
# ==============

type GroupsSnapshot = list[int | GroupsSnapshot]


class ChoiceDB(CreatedAtMixin, Base):
    """Заполненная форма с выбором карточек в архитектурном проекте."""

    __tablename__ = "user_choices"

    id: Mapped[int] = mapped_column(IDENTITY, primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))

    # Relations
    user: Mapped[UserDB] = relationship(back_populates="choices")
    groups: Mapped[list[GroupSnapshotDB]] = relationship(
        cascade="all, delete, delete-orphan",
        passive_deletes=True,
        lazy="selectin",
        order_by="GroupSnapshotDB.ordinal_no",
    )


class GroupSnapshotDB(Base):
    __tablename__ = "user_item_choice_groups"

    id: Mapped[int] = mapped_column(IDENTITY, primary_key=True)
    choice_id: Mapped[int] = mapped_column(
        ForeignKey("user_choices.id", ondelete="CASCADE")
    )
    group_id: Mapped[int | None] = mapped_column(
        ForeignKey("user_item_choice_groups.id", ondelete="CASCADE")
    )
    ordinal_no: Mapped[int]

    name: Mapped[str] = mapped_column(String(256))

    # Relations
    items: Mapped[list[ItemChoiceDB]] = relationship(
        cascade="all, delete, delete-orphan",
        passive_deletes=True,
        lazy="selectin",
        order_by="ItemChoiceDB.ordinal_no",
    )
    subgroups: Mapped[list[GroupSnapshotDB]] = relationship(
        cascade="all, delete, delete-orphan",
        passive_deletes=True,
        lazy="selectin",
        order_by="GroupSnapshotDB.ordinal_no",
    )


class ItemChoiceDB(ItemTableBase, Base):
    """Выбор конкретной карточки в рамках формы."""

    __tablename__ = "user_item_choices"

    group_id: Mapped[int] = mapped_column(
        ForeignKey("user_item_choice_groups.id"), primary_key=True
    )
    ordinal_no: Mapped[int] = mapped_column(primary_key=True)
    item_id: Mapped[int | None] = mapped_column(
        ForeignKey("project_spec_items.id", ondelete="SET NULL")
    )

    tags: Mapped[list[str]] = mapped_column(JsonType)


# ============
# Files Domain
# ============

CONTENT_TYPE_ENUM = Enum(
    ContentType,
    name="content_Type_enum",
    # pyrefly: ignore[implicit-any-lambda]
    values_callable=lambda obj: [item.value for item in obj],  # pyright: ignore[reportUnknownLambdaType, reportUnknownMemberType, reportUnknownVariableType]
)


class StorageObjectDB(TimestampMixin, Base):
    __tablename__ = "storage_objects"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID, primary_key=True, default=uuid.uuid4
    )
    blob_id: Mapped[uuid.UUID] = mapped_column(GUID, default=uuid.uuid4)

    size: Mapped[int]
    sha256: Mapped[str] = mapped_column(String(64))

    etag: Mapped[str] = mapped_column(String(32))
    original_filename: Mapped[str | None] = mapped_column(String(1024))
    content_type: Mapped[ContentType | None] = mapped_column(CONTENT_TYPE_ENUM)


class ImageDB(Base):
    __tablename__ = "images"

    id: Mapped[int] = mapped_column(IDENTITY, primary_key=True)
    object_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("storage_objects.id", ondelete="CASCADE")
    )

    width: Mapped[int] = mapped_column(SmallInteger)
    height: Mapped[int] = mapped_column(SmallInteger)

    quality: Mapped[int] = mapped_column(SmallInteger)
