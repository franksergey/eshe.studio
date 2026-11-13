import logging
from collections.abc import Sequence
from decimal import Decimal
from enum import StrEnum
from typing import Annotated, Any, Literal

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
    ValidationInfo,
    field_validator,
    model_validator,
)

from server.domain.files.schemas import ImageRef
from server.domain.users.schemas import UserID

logger = logging.getLogger(__name__)

# ========================
# Aggregate Root: Projects
# ========================


type ProjectID = int


class ProjectBase(BaseModel):
    """Базовая модель проекта."""

    name: Annotated[str, Field(min_length=1, max_length=256)]

    model_config = ConfigDict(from_attributes=True, serialize_by_alias=True)


class ProjectPure(ProjectBase):
    """Изолированная модель проекта."""

    id: ProjectID


class Project(ProjectPure):
    """Проект с таблицей комплектации."""

    categories: Annotated[list[Group], Field(max_length=64)]


# ==========================
# Intermediate entity: Group
# ==========================


class ItemType(StrEnum):
    ITEM = "item"
    GROUP = "group"


type GroupID = int


class GroupBase(BaseModel):
    """Базовая модель группы карточек."""

    name: Annotated[str, Field(min_length=1, max_length=256)]

    model_config = ConfigDict(
        use_enum_values=True, from_attributes=True, serialize_by_alias=True
    )


class GroupPure(GroupBase):
    """Модель для группы без внешних связей."""

    id: GroupID


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


class ItemStatus(StrEnum):
    APPROVED = "approved"
    PAID = "paid"


class ItemBase(BaseModel):
    """Базовая модель для карточки."""

    name: Annotated[str, Field(min_length=1, max_length=1024)]
    count: int = Field(default=1, ge=1, le=256)
    price: MoneyType | None = None

    @model_validator(mode="before")
    @classmethod
    def _validate_price(cls, v: object) -> object:
        error_msg = (
            "Both 'price' and 'price_currency' must be provided together."
        )

        if isinstance(v, dict) and "price" in v and "price_currency" in v:
            price: Any = v.get("price")
            price_currency: Any = v.get("price_currency")

            if (price is None) != (price_currency is None):
                raise ValueError(error_msg)

            if price is not None and price_currency is not None:
                v["price"] = MoneyType(amount=price, currency=price_currency)

        elif hasattr(v, "price") and hasattr(v, "price_currency"):
            price: Any = v.price
            price_currency: Any = v.price_currency

            if (price is None) != (price_currency is None):
                raise ValueError(error_msg)

            if price is not None and price_currency is not None:
                # pyrefly: ignore[missing-attribute]
                v.price = MoneyType(
                    amount=Decimal(price), currency=price_currency
                )

        return v

    link: HttpUrl | None = None
    tags: list[str] = Field(default_factory=list[str], max_length=16)

    @model_validator(mode="before")
    @classmethod
    def _validate_tags(cls, v: object) -> object:
        error_msg = "'tags' must be a list of strings."

        if isinstance(v, dict) and "tags" in v:
            tags: Any = v.get("tags")

            if not isinstance(tags, Sequence):
                raise ValueError(error_msg)

            v["tags"] = [str(tag) for tag in tags]

        elif hasattr(v, "tags"):
            tags: Any = v.tags

            if not isinstance(tags, Sequence):
                raise ValueError(error_msg)

            # pyrefly: ignore[missing-attribute]
            v.tags = [str(tag) for tag in tags]

        return v

    status: ItemStatus | None = None

    model_config = ConfigDict(
        use_enum_values=True, from_attributes=True, serialize_by_alias=True
    )


class ItemPure(ItemBase):
    """Модель карточки без внешних связей."""

    id: ItemID


class Item(ItemPure):
    """Вариант предмета в таблице комплектации (карточка)."""

    item_type: Literal[ItemType.ITEM] = ItemType.ITEM

    image: HttpUrl | None

    @field_validator("image", mode="before")
    @classmethod
    def _validate_image(cls, v: object, info: ValidationInfo) -> object:
        if not (info.context and "get_image_url" in info.context):
            return v

        if v is None:
            return None

        image = ImageRef.model_validate(v)
        return info.context["get_image_url"](image)


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


type CommentID = int


class CommentBase(BaseModel):
    """Базовая модель комментария."""

    text: Annotated[str, Field(min_length=1, max_length=4096)]


class CommentCreate(CommentBase):
    """Модель создания комментария."""


class Comment(CommentBase):
    """Комментарий к элементу комплектации."""

    id: CommentID
    user_id: UserID | None
    author_name: str

    created_at: AwareDatetime


class CommentsBulkRead(BaseModel):
    items: list[ItemOnlyComments]
    item_ids_not_found: list[ItemID]


ItemBase.model_rebuild()
