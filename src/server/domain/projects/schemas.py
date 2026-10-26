from decimal import Decimal
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, HttpUrl

from server.domain.users.schemas import UserID

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


class GroupPure(GroupBase):
    """Модель для группы без внешних связей."""

    id: int


class GroupOnlyItems(GroupPure):
    """Группа с внешней связью групп и карточек."""

    items: list[Item] | list[Group]

    @property
    def has_items(self) -> bool:
        if not self.items:
            return False

        return isinstance(self.items[0], Item)

    @property
    def has_groups(self) -> bool:
        if not self.items:
            return False

        return isinstance(self.items[0], Group)


class Group(GroupOnlyItems):
    """Группа карточек в таблице комплектации.

    Самый верхний уровень групп – это "категории" товаров.
    """

    item_type: Literal[ItemType.GROUP] = ItemType.GROUP


# ===============
# Tree leaf: Item
# ===============

type ItemID = int


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

    id: ItemID

    approved: bool


class Item(ItemPure):
    """Вариант предмета в таблице комплектации (карточка)."""

    item_type: Literal[ItemType.ITEM] = ItemType.ITEM

    image: HttpUrl | None


class ItemOnlyComments(BaseModel):
    id: ItemID
    comments: list[Comment]


class CurrencyCode(StrEnum):
    def get_symbol(self) -> str:
        return CURRENCY_SYMBOLS_TABLE[self]

    RUB = "RUB"
    USD = "USD"
    EUR = "EUR"


CURRENCY_SYMBOLS_TABLE: dict[CurrencyCode, str] = {
    CurrencyCode.RUB: "&#x20bd;",
    CurrencyCode.USD: "&dollar;",
    CurrencyCode.EUR: "&euro;",
}


class MoneyType(BaseModel):
    amount: Annotated[Decimal, Field(ge=Decimal(0))]
    currency: CurrencyCode

    @staticmethod
    def format_decimal(d: Decimal, sep: str = "&nbsp;") -> str:
        integral = d.to_integral_value()

        s = f"{integral:,f}" if d == integral else f"{d.normalize():,f}"
        return s.replace(",", sep)

    @property
    def html_formatted(self) -> str:
        return (
            f"{self.format_decimal(self.amount)}&nbsp;"
            f"{self.currency.get_symbol()}"
        )


class CommentBase(BaseModel):
    """Базовая модель комментария."""

    text: Annotated[str, Field(min_length=1, max_length=4096)]


class CommentCreate(CommentBase):
    """Модель создания комментария."""


class Comment(CommentBase):
    """Комментарий к элементу комплектации."""

    id: int
    user_id: UserID | None
    author_name: str

    created_at: AwareDatetime


class CommentsBulkRead(BaseModel):
    items: list[ItemOnlyComments]
    item_ids_not_found: list[int]


ItemBase.model_rebuild()
