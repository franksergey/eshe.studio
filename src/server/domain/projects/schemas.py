from decimal import Decimal
from enum import StrEnum
from typing import Annotated

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, HttpUrl

# =============================
# Aggregate Root: Specification
# =============================


class ProjectBase(BaseModel):
    """Базовая модель таблицы комплектации."""

    name: Annotated[str, Field(min_length=1, max_length=256)]

    model_config = ConfigDict(from_attributes=True, serialize_by_alias=True)


class ProjectCreate(ProjectBase):
    """Модель для создания спецификации."""


class ProjectPut(ProjectBase):
    """Модель для полной замены объекта спецификации."""


class ProjectUpdate(BaseModel):
    """Модель для частичного обновления объекта спецификации."""

    name: Annotated[str | None, Field(None, min_length=1, max_length=256)]

    model_config = ConfigDict(from_attributes=True, serialize_by_alias=True)


class ProjectPure(ProjectBase):
    """Изолированная модель таблицы комплектации."""

    id: int


class Project(ProjectPure):
    """Таблица комплектации."""

    rooms: Annotated[list[Room], Field(max_length=64)]


class CurrencyCode(StrEnum):
    RUB = "RUB"
    USD = "USD"
    EUR = "EUR"


class MoneyType(BaseModel):
    amount: Annotated[Decimal, Field(ge=Decimal(0))]
    currency: CurrencyCode


class CommentBase(BaseModel):
    """Базовая модель комментария."""

    text: Annotated[str, Field(min_length=1, max_length=4096)]
    author_name: Annotated[str, Field(min_length=1)]


class CommentCreate(CommentBase):
    """Модель создания комментария."""


class Comment(CommentBase):
    """Комментарий к элементу комплектации."""

    id: int

    created_at: AwareDatetime


class Item(BaseModel):
    """Вариант предмета в таблице комплектации."""

    name: Annotated[str, Field(min_length=1, max_length=1024)]
    count: Annotated[int, Field(ge=1, le=256)]

    link: HttpUrl | None = None
    tags: Annotated[list[str], Field(max_length=16)]

    price: MoneyType | None
    comments: list[Comment]

    model_config = ConfigDict(
        use_enum_values=True, from_attributes=True, serialize_by_alias=True
    )


class Category(BaseModel):
    """Категория предметов в таблице комплектации."""

    name: Annotated[str, Field(min_length=1, max_length=1024)]
    items: Annotated[list[Item], Field(min_length=1, max_length=32)]

    model_config = ConfigDict(from_attributes=True, serialize_by_alias=True)


class Room(BaseModel):
    """Комната, для которой выбираются предметы в таблице комплектации."""

    name: Annotated[str, Field(min_length=1, max_length=256)]
    categories: Annotated[list[Category], Field(min_length=1, max_length=64)]

    model_config = ConfigDict(from_attributes=True, serialize_by_alias=True)
