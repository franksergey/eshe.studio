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
    item: Mapped[SpecificationItemDB] = relationship(back_populates="tags")


PYDANTIC_MAX_URL_LENGTH = 2083
CURRENCY_CODE_ENUM = Enum(CurrencyCode, name="currency_code_enum")


class SpecificationItemDB(Base):
    __tablename__ = "specification_items"

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(String(1024))
    count: Mapped[int] = mapped_column(SmallInteger)

    link: Mapped[str] = mapped_column(String(PYDANTIC_MAX_URL_LENGTH))

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
    )

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "(price IS NULL AND price_currency IS NULL) "
            "OR NOT(price IS NULL OR price_currency IS NULL)",
            name="ux_c_email_or_phone_required",
        ),
    )
