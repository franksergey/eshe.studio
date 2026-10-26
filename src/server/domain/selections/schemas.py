import uuid

from pydantic import AwareDatetime, BaseModel, ConfigDict

from server.domain.projects.schemas import ItemID


class SelectionCreate(BaseModel):
    item_ids: list[ItemID]

    model_config = ConfigDict(from_attributes=True, serialize_by_alias=True)


class SelectionPure(BaseModel):
    id: int

    user_id: uuid.UUID
    created_at: AwareDatetime
    updated_at: AwareDatetime

    model_config = ConfigDict(from_attributes=True, serialize_by_alias=True)


class Selection(SelectionPure):
    items: list[ItemID]
