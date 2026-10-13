from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

from server.domain.projects.schemas import ItemBase, ItemType
from server.domain.users.schemas import UserRead


class ChoiceCreate(BaseModel):
    item_ids: list[int]

    model_config = ConfigDict(from_attributes=True, serialize_by_alias=True)


class Choice(BaseModel):
    id: int

    user: UserRead
    items: list[GroupSnapshot]

    model_config = ConfigDict(from_attributes=True, serialize_by_alias=True)


class GroupSnapshot(BaseModel):
    item_type: Literal[ItemType.GROUP] = ItemType.GROUP

    name: Annotated[str, Field(min_length=1, max_length=256)]

    items: list[
        Annotated[ItemChoice | GroupSnapshot, Field(discriminator="item_type")]
    ]

    model_config = ConfigDict(
        use_enum_values=True, from_attributes=True, serialize_by_alias=True
    )


class ItemChoice(ItemBase, BaseModel):
    item_type: Literal[ItemType.ITEM] = ItemType.ITEM

    item_id: int | None

    approved: bool

    model_config = ConfigDict(
        use_enum_values=True, from_attributes=True, serialize_by_alias=True
    )
