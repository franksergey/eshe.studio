from decimal import Decimal
from typing import ClassVar

from sqlalchemy import ForeignKey, MetaData, Numeric, SmallInteger, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

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
        ForeignKey("specification_items.id"), primary_key=True
    )
    ordinal_no: Mapped[int] = mapped_column(primary_key=True)
    tag: Mapped[str] = mapped_column(String(255))


class SpecificationItemDB(Base):
    __tablename__ = "specification_items"

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str]
    count: Mapped[int] = mapped_column(SmallInteger)

    link: Mapped[str]

    price: Mapped[Decimal] = mapped_column(Numeric(precision=12, scale=2))
    price_currency: Mapped[CurrencyCode]
