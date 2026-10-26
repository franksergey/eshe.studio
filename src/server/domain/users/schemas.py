import uuid
from typing import Annotated

from fastapi_users.schemas import BaseUser, BaseUserCreate, BaseUserUpdate
from pydantic import Field, computed_field

type UserID = uuid.UUID


class UserRead(BaseUser[UserID]):
    hashed_password: Annotated[str, Field(exclude=True)]

    first_name: str
    last_name: str | None

    @computed_field
    def full_name(self) -> str:
        if self.last_name is None:
            return self.first_name

        return f"{self.first_name} {self.last_name}"


NAME_FIELD = Field(min_length=1, max_length=64)


class UserCreate(BaseUserCreate):
    first_name: Annotated[str, NAME_FIELD]
    last_name: Annotated[str | None, NAME_FIELD]


class UserUpdate(BaseUserUpdate):
    first_name: Annotated[str, NAME_FIELD]
    last_name: Annotated[str | None, NAME_FIELD]
