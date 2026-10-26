import uuid

from fastapi_users.schemas import BaseUser, BaseUserCreate, BaseUserUpdate

type UserID = uuid.UUID


class UserRead(BaseUser[UserID]):
    @property
    def first_name(self) -> str:
        return self.email


class UserCreate(BaseUserCreate):
    pass


class UserUpdate(BaseUserUpdate):
    pass
