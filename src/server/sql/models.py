from decimal import Decimal
from typing import ClassVar

from sqlalchemy import (
    CheckConstraint,
    Enum,
    ForeignKey,
    MetaData,
    Numeric,
    SmallInteger,
    String,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from server.services.schemas import CurrencyCode


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


class SpecificationTagDB(Base):
    __tablename__ = "specification_tag"

    item_id: Mapped[int] = mapped_column(
        ForeignKey("specification_items.id", ondelete="CASCADE"),
        primary_key=True,
    )
    ordinal_no: Mapped[int] = mapped_column(primary_key=True)

    tag: Mapped[str] = mapped_column(String(255))

    # Relations
    item: Mapped[ItemDB] = relationship(back_populates="tags")


PYDANTIC_MAX_URL_LENGTH = 2083
CURRENCY_CODE_ENUM = Enum(CurrencyCode, name="currency_code_enum")


class ItemDB(Base):
    """Вариант предмета в таблице комплектации."""

    __tablename__ = "specification_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    category_id: Mapped[int] = mapped_column(
        ForeignKey("specification_items_categories.id", ondelete="CASCADE")
    )
    ordinal_no: Mapped[int] = mapped_column()

    name: Mapped[str] = mapped_column(String(1024))
    count: Mapped[int] = mapped_column(SmallInteger)

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
    category: Mapped[CategoryDB] = relationship(back_populates="items")

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "(price IS NULL AND price_currency IS NULL) "
            "OR NOT(price IS NULL OR price_currency IS NULL)",
            name="ux_c_email_or_phone_required",
        ),
    )


class CategoryDB(Base):
    """Категория предметов в таблице комплектации."""

    __tablename__ = "specification_items_categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    room_id: Mapped[int] = mapped_column(
        ForeignKey("specification_rooms.id", ondelete="CASCADE")
    )

    name: Mapped[str] = mapped_column(String(1024))
    ordinal_no: Mapped[int] = mapped_column()

    # Relations
    items: Mapped[list[ItemDB]] = relationship(
        back_populates="category",
        cascade="all, delete, delete-orphan",
        passive_deletes=True,
        lazy="joined",
        order_by=ItemDB.ordinal_no,
    )
    room: Mapped[RoomDB] = relationship(back_populates="categories")


class RoomDB(Base):
    """Комната, для которой выбираются предметы в таблице комплектации."""

    __tablename__ = "specification_rooms"

    id: Mapped[int] = mapped_column(primary_key=True)
    specification_id: Mapped[int] = mapped_column(
        ForeignKey("specifications.id", ondelete="CASCADE")
    )

    name: Mapped[str] = mapped_column(String(256))
    ordinal_no: Mapped[int] = mapped_column()

    # Relations
    categories: Mapped[list[CategoryDB]] = relationship(
        back_populates="room",
        cascade="all, delete, delete-orphan",
        passive_deletes=True,
        lazy="joined",
        order_by=CategoryDB.ordinal_no,
    )
    specification: Mapped[SpecificationDB] = relationship(
        back_populates="rooms"
    )


class SpecificationDB(Base):
    """Таблица комплектации."""

    __tablename__ = "specifications"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Or location?
    name: Mapped[str] = mapped_column(String(256))

    # Relations
    rooms: Mapped[list[RoomDB]] = relationship(
        back_populates="specification",
        cascade="all, delete, delete-orphan",
        passive_deletes=True,
        lazy="joined",
        order_by=RoomDB.ordinal_no,
    )
