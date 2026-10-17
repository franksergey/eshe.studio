import uuid

from fastapi_users.schemas import BaseUser, BaseUserCreate, BaseUserUpdate


class UserRead(BaseUser[uuid.UUID]):
    @property
    def first_name(self) -> str:
        return self.email


class UserCreate(BaseUserCreate):
    pass


class UserUpdate(BaseUserUpdate):
    pass
