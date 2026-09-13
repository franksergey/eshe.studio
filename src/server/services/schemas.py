from decimal import Decimal
from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class CurrencyCode(StrEnum):
    RUB = "RUB"
    USD = "USD"
    EUR = "EUR"


class MoneyType(BaseModel):
    amount: Annotated[Decimal | None, Field(ge=Decimal(0))]
    currency: CurrencyCode | None


class Item(BaseModel):
    """Вариант предмета в таблице комплектации."""

    name: Annotated[str, Field(min_length=1, max_length=1024)]
    count: Annotated[int, Field(ge=1, le=256)]

    link: HttpUrl | None = None
    tags: Annotated[list[str], Field(max_length=16)]

    price: MoneyType | None

    model_config = ConfigDict(use_enum_values=True)


class Category(BaseModel):
    """Категория предметов в таблице комплектации."""

    name: Annotated[str, Field(min_length=1, max_length=1024)]

    items: Annotated[list[Item], Field(min_length=1, max_length=32)]


class Room(BaseModel):
    """Комната, для которой выбираются предметы в таблице комплектации."""

    name: Annotated[str, Field(min_length=1, max_length=256)]

    categories: Annotated[list[Category], Field(min_length=1, max_length=64)]


class Specification(BaseModel):
    """Таблица комплектации."""

    name: Annotated[str, Field(min_length=1, max_length=256)]

    rooms: Annotated[list[Room], Field(min_length=1, max_length=64)]
