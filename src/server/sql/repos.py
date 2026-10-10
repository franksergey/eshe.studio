from dataclasses import dataclass
from typing import TYPE_CHECKING, cast, override

from fastapi_users import exceptions
from pydantic import HttpUrl
from sqlalchemy import exists, select
from sqlalchemy.orm import lazyload, load_only, selectinload

from server.api.errors import UserAlreadyExistsError
from server.domain.projects.ports import AbstractProjectsRepo
from server.domain.projects.schemas import (
    Category,
    Comment,
    CommentCreate,
    CurrencyCode,
    Item,
    MoneyType,
    Project,
    ProjectPure,
    Room,
)
from server.domain.users.ports import AbstractUsersRepo
from server.domain.users.schemas import UserRead
from server.sql.models import (
    CategoryDB,
    CommentDB,
    ItemDB,
    ProjectDB,
    RoomDB,
    UserDB,
)

if TYPE_CHECKING:
    import uuid

    from fastapi import Request
    from fastapi_users.db import SQLAlchemyUserDatabase
    from sqlalchemy.ext.asyncio import AsyncSession

    from server.api.auth import UserManager
    from server.domain.users.schemas import UserCreate, UserUpdate


class ProjectsRepo(AbstractProjectsRepo):
    session: AsyncSession

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @classmethod
    def _validate_comment(cls, obj: CommentDB) -> Comment:
        return Comment(
            id=obj.id,
            text=obj.text,
            author_name=obj.author_name,
            created_at=obj.created_at,
        )

    @classmethod
    def _validate_item(cls, obj: ItemDB) -> Item:
        if obj.price is None:
            price = None
        else:
            price = MoneyType(
                amount=obj.price,
                currency=cast("CurrencyCode", obj.price_currency),
            )

        return Item(
            name=obj.name,
            count=obj.count,
            link=HttpUrl(obj.link) if obj.link is not None else None,
            tags=[tag.tag for tag in obj.tags],
            price=price,
            comments=[
                cls._validate_comment(comment) for comment in obj.comments
            ],
        )

    @classmethod
    def _validate_category(cls, obj: CategoryDB) -> Category:
        return Category(
            name=obj.name,
            items=[cls._validate_item(item) for item in obj.items],
        )

    @classmethod
    def _validate_room(cls, obj: RoomDB) -> Room:
        return Room(
            name=obj.name,
            categories=[
                cls._validate_category(category) for category in obj.categories
            ],
        )

    @classmethod
    def _to_domain_schema(cls, obj: ProjectDB) -> Project:
        return Project(
            id=obj.id,
            name=obj.name,
            rooms=[cls._validate_room(room) for room in obj.rooms],
        )

    @staticmethod
    def _to_domain_schema_pure(obj: ProjectDB) -> ProjectPure:
        return ProjectPure(id=obj.id, name=obj.name)

    @override
    async def get(self, id: int) -> Project | None:
        stmt = select(ProjectDB).where(ProjectDB.id == id)
        obj = await self.session.scalar(stmt)

        if obj is None:
            return None

        return self._to_domain_schema(obj)

    GET_ALL_STMT = select(ProjectDB)

    @override
    async def get_all(self) -> list[Project]:
        objs = (await self.session.scalars(self.GET_ALL_STMT)).all()

        return [self._to_domain_schema(obj) for obj in objs]

    GET_ALL_PURE_STMT = select(ProjectDB).options(lazyload(ProjectDB.rooms))

    @override
    async def get_all_pure(self) -> list[ProjectPure]:
        objs = (await self.session.scalars(self.GET_ALL_PURE_STMT)).all()

        return [self._to_domain_schema_pure(obj) for obj in objs]

    @override
    async def check_item_exists(self, item_id: int) -> bool:
        stmt = select(exists(ItemDB).where(ItemDB.id == item_id))
        return (await self.session.execute(stmt)).scalar_one()

    @override
    async def get_item_comments(self, item_id: int) -> list[Comment] | None:
        stmt = (
            select(ItemDB)
            .options(load_only(ItemDB.id), selectinload(ItemDB.comments))
            .where(ItemDB.id == item_id)
        )
        obj = await self.session.scalar(stmt)

        if obj is None:
            return None

        return [self._validate_comment(comment) for comment in obj.comments]

    # NOTE: Should it return new data of ItemDB?
    @override
    async def add_comment(
        self, item_id: int, data: CommentCreate
    ) -> Comment | None:
        stmt = select(ItemDB).where(ItemDB.id == item_id)
        item = await self.session.scalar(stmt)

        if item is None:
            return None

        obj = CommentDB(text=data.text, author_name=data.author_name)
        item.comments.append(obj)
        await self.session.flush((item,))

        return self._validate_comment(obj)


@dataclass(eq=False, slots=True)
class UsersRepo(AbstractUsersRepo):
    users_db: SQLAlchemyUserDatabase[UserDB, uuid.UUID]
    user_manager: UserManager
    request: Request

    @staticmethod
    def _to_domain_schema(user: UserDB) -> UserRead:
        return UserRead(
            id=user.id,
            email=user.email,
            is_active=user.is_active,
            is_superuser=user.is_superuser,
            is_verified=user.is_verified,
        )

    async def get(self, id: uuid.UUID) -> UserRead | None:
        user = await self.users_db.get(id)

        if user is None:
            return None

        return self._to_domain_schema(user)

    async def get_by_email(self, user_email: str) -> UserRead | None:
        user = await self.users_db.get_by_email(user_email)

        if user is None:
            return None

        return self._to_domain_schema(user)

    async def create(
        self, data: UserCreate, *, safe: bool = False
    ) -> UserRead:
        try:
            return self._to_domain_schema(
                await self.user_manager.create(
                    data, safe=safe, request=self.request
                )
            )
        except exceptions.UserAlreadyExists as exc:
            raise UserAlreadyExistsError from exc

    async def update(
        self, user_email: str, data: UserUpdate, *, safe: bool = False
    ) -> UserRead | None:
        user = await self.users_db.get_by_email(user_email)

        if user is None:
            return None

        return self._to_domain_schema(
            await self.user_manager.update(
                data, user, safe=safe, request=self.request
            )
        )

    async def delete(self, user_email: str) -> UserRead | None:
        user = await self.users_db.get_by_email(user_email)

        if user is None:
            return None

        await self.user_manager.delete(user, self.request)
        return self._to_domain_schema(user)
