import uuid
from typing import Annotated

from fastapi_users.schemas import BaseUser, BaseUserCreate, BaseUserUpdate
from pydantic import Field

type UserID = uuid.UUID


class UserRead(BaseUser[UserID]):
    hashed_password: Annotated[str, Field(exclude=True)]

    @property
    def first_name(self) -> str:
        return self.email


class UserCreate(BaseUserCreate):
    pass


class UserUpdate(BaseUserUpdate):
    pass
