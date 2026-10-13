from decimal import Decimal
from typing import ClassVar

from fastapi_users.db import SQLAlchemyBaseUserTableUUID
from sqlalchemy import (
    CheckConstraint,
    Enum,
    ForeignKey,
    Identity,
    MetaData,
    Numeric,
    SmallInteger,
    String,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from server.config import settings
from server.domain.projects.schemas import CurrencyCode
from server.sql.mixins import CreatedAtMixin


class Base(DeclarativeBase):
    metadata: ClassVar[MetaData] = MetaData(
        naming_convention={
            "ix": "ix_%(table_name)s_%(column_0_label)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_%(constraint_name)s",
            "fk": (
                "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s"
            ),
            "pk": "pk_%(table_name)s",
        }
    )


IDENTITY = (
    Identity(always=True) if settings.db.DIALECT == "postgresql" else None
)


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


class ItemDB(Base):
    """Вариант предмета в таблице комплектации."""

    __tablename__ = "project_spec_items"

    id: Mapped[int] = mapped_column(IDENTITY, primary_key=True)
    group_id: Mapped[int] = mapped_column(
        ForeignKey("project_spec_groups.id", ondelete="CASCADE")
    )
    ordinal_no: Mapped[int] = mapped_column()

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

    # Relations
    tags: Mapped[list[SpecificationTagDB]] = relationship(
        back_populates="item",
        cascade="all, delete, delete-orphan",
        passive_deletes=True,
        lazy="joined",
        order_by=SpecificationTagDB.ordinal_no,
    )
    comments: Mapped[list[CommentDB]] = relationship(
        back_populates="item",
        cascade="all, delete, delete-orphan",
        passive_deletes=True,
        lazy="joined",
    )
    group: Mapped[GroupDB] = relationship(back_populates="items")

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
        order_by="GroupDB.ordinal_no",
    )
    parent_group: Mapped[GroupDB | None] = relationship(
        back_populates="subgroups", remote_side="GroupDB.id"
    )
    project: Mapped[ProjectDB] = relationship(back_populates="categories")


class ProjectDB(Base):
    """Архитектурный проект."""

    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(IDENTITY, primary_key=True)

    # Or location?
    name: Mapped[str] = mapped_column(String(256))

    # Relations
    categories: Mapped[list[GroupDB]] = relationship(
        back_populates="project",
        cascade="all, delete, delete-orphan",
        passive_deletes=True,
        lazy="joined",
        order_by=GroupDB.ordinal_no,
    )


# ============
# Users Domain
# ============


class UserDB(SQLAlchemyBaseUserTableUUID, Base):
    __tablename__ = "users"
