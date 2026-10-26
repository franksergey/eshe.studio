from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

from server.domain.projects.schemas import ItemID
from server.domain.users.schemas import UserID


class SelectionCreate(BaseModel):
    item_ids: set[ItemID]
    deselect_item_ids: set[ItemID] | None = Field(None)

    model_config = ConfigDict(from_attributes=True, serialize_by_alias=True)


class SelectionPure(BaseModel):
    id: int

    user_id: UserID
    created_at: AwareDatetime
    updated_at: AwareDatetime

    model_config = ConfigDict(from_attributes=True, serialize_by_alias=True)


class Selection(SelectionPure):
    items: list[ItemID]
