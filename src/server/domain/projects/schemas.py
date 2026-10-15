from decimal import Decimal
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, HttpUrl

# ========================
# Aggregate Root: Projects
# ========================


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

    name: Annotated[str, Field(min_length=1, max_length=256)] = ""

    model_config = ConfigDict(from_attributes=True, serialize_by_alias=True)


class ProjectPure(ProjectBase):
    """Изолированная модель таблицы комплектации."""

    id: int


class Project(ProjectPure):
    """Таблица комплектации."""

    categories: Annotated[list[Group], Field(max_length=64)]


# ==========================
# Intermediate entity: Group
# ==========================


class ItemType(StrEnum):
    ITEM = "item"
    GROUP = "group"


class GroupBase(BaseModel):
    """Базовая модель группы карточек."""

    name: Annotated[str, Field(min_length=1, max_length=256)]

    model_config = ConfigDict(
        use_enum_values=True, from_attributes=True, serialize_by_alias=True
    )


class GroupCreate(GroupBase):
    """Модель для создания новой группы."""


class GroupPut(GroupBase):
    """Модель для полного обновления группы."""


class Group(GroupBase):
    """Группа карточек в таблице комплектации.

    Самый верхний уровень групп – это "категории" товаров.
    """

    item_type: Literal[ItemType.GROUP] = ItemType.GROUP

    items: list[Annotated[Item | Group, Field(discriminator="item_type")]]


# ===============
# Tree leaf: Item
# ===============


class ItemBase(BaseModel):
    """Базовая модель для карточки."""

    name: Annotated[str, Field(min_length=1, max_length=1024)]
    count: Annotated[int, Field(ge=1, le=256)]
    price: MoneyType | None

    link: HttpUrl | None = None
    tags: Annotated[list[str], Field(max_length=16)]

    model_config = ConfigDict(
        use_enum_values=True, from_attributes=True, serialize_by_alias=True
    )


class ItemCreate(ItemBase):
    """Модель для создания карточки."""


class ItemPut(ItemBase):
    """Модель для полного обновления карточки."""


class ItemUpdate(BaseModel):
    """Модель для частичного обновления карточки."""

    name: Annotated[str, Field(min_length=1, max_length=1024)] = ""
    count: Annotated[int, Field(ge=1, le=256)] = 1
    price: MoneyType | None = None

    link: HttpUrl | None = None
    tags: Annotated[list[str], Field(max_length=16)] = []

    model_config = ConfigDict(
        use_enum_values=True, from_attributes=True, serialize_by_alias=True
    )


class ItemPure(ItemBase):
    """Модель карточки без внешних связей."""

    id: int

    approved: bool


class ItemWithComments(ItemPure):
    comments: list[Comment]


class Item(ItemPure):
    """Вариант предмета в таблице комплектации (карточка)."""

    item_type: Literal[ItemType.ITEM] = ItemType.ITEM


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


ItemBase.model_rebuild()
