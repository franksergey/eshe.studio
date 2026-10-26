from typing import Annotated, Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

from server.domain.projects.schemas import ItemBase, ItemType
from server.domain.users.schemas import UserID


class ChoiceCreate(BaseModel):
    item_ids: list[int]

    model_config = ConfigDict(from_attributes=True, serialize_by_alias=True)


class ChoicePure(BaseModel):
    id: int

    user_id: UserID
    created_at: AwareDatetime

    model_config = ConfigDict(from_attributes=True, serialize_by_alias=True)


class Choice(ChoicePure):
    items: list[GroupSnapshot]


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
