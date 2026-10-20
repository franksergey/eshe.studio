import asyncio
import logging
from contextlib import AbstractAsyncContextManager
from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol, Self, override

from sqlalchemy.exc import DBAPIError

from server.domain.choices.services import ChoicesService
from server.domain.files.service import FilesService
from server.domain.projects.service import ProjectsService
from server.domain.users.service import UsersService
from server.sql.models import UserDB
from server.sql.repos import ProjectsRepo, UserDatabase, UsersRepo
from server.sql.repos.choices import ChoicesRepo
from server.sql.repos.files import LocalObjectsStorage

from .auth import UserManager

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from fastapi import Request
    from sqlalchemy.ext.asyncio import AsyncSession


logger = logging.getLogger(__name__)


@dataclass(eq=False, slots=True)
class ServiceContainer(AbstractAsyncContextManager["ServiceContainer"]):
    _get_session: Callable[[], AsyncSession]

    session: AsyncSession
    request: Request | None
    storage_dir: Path

    def __init__(
        self,
        get_session: Callable[[], AsyncSession],
        storage_dir: Path,
        request: Request | None = None,
    ) -> None:
        self._get_session = get_session
        self.request = request
        self.storage_dir = storage_dir

        self._projects_service = None
        self._choices_service = None
        self._users_service = None
        self._files_service = None
        self._objects_storage = None
        self._user_db = None
        self._user_manager = None

    @override
    async def __aenter__(self) -> Self:
        self.session = self._get_session()
        return self

    @override
    async def __aexit__(
        self, exc_type: object, exc: object, tb: object
    ) -> bool:
        try:
            if exc_type is None:
                await asyncio.shield(self._commit())
            else:
                await asyncio.shield(self._rollback())
        finally:
            await asyncio.shield(self.session.close())

        return False

    @staticmethod
    def _commit_outcome_unknown(exc: BaseException) -> bool:
        if isinstance(exc, asyncio.CancelledError):
            return True

        return isinstance(exc, DBAPIError) and exc.connection_invalidated

    async def _commit(self) -> None:
        try:
            await asyncio.shield(self.session.commit())
        except BaseException as exc:
            await asyncio.shield(
                self._rollback(
                    commit_outcome_unknown=self._commit_outcome_unknown(exc)
                )
            )
            raise

        if self._objects_storage is not None:
            await asyncio.shield(self._objects_storage.confirm())

    async def _rollback(self, *, commit_outcome_unknown: bool = False) -> None:
        try:
            await asyncio.shield(self.session.rollback())
        except Exception:
            logger.exception("Failed to rollback SQLAlchemy session")

        if self._objects_storage is not None:
            if commit_outcome_unknown:
                self._objects_storage.forget()
            else:
                await asyncio.shield(self._objects_storage.rollback())

    _projects_service: ProjectsService | None

    @property
    def projects(self) -> ProjectsService:
        if self._projects_service is None:
            repo = ProjectsRepo(self.session)
            self._projects_service = ProjectsService(repo)

        return self._projects_service

    _choices_service: ChoicesService | None

    @property
    def choices(self) -> ChoicesService:
        if self._choices_service is None:
            repo = ChoicesRepo(self.session)
            self._choices_service = ChoicesService(repo)

        return self._choices_service

    _users_service: UsersService | None

    @property
    def users(self) -> UsersService:
        if self._users_service is None:
            repo = UsersRepo(self.user_db, self.user_manager, self.request)
            self._users_service = UsersService(repo)

        return self._users_service

    _files_service: FilesService | None
    _objects_storage: LocalObjectsStorage | None

    @property
    def files(self) -> FilesService:
        if self._files_service is None:
            self._objects_storage = LocalObjectsStorage(
                self.session, self.storage_dir
            )
            self._files_service = FilesService(self._objects_storage)

        return self._files_service

    _user_db: UserDatabase | None

    @property
    def user_db(self) -> UserDatabase:
        if self._user_db is None:
            self._user_db = UserDatabase(self.session, UserDB)

        return self._user_db

    _user_manager: UserManager | None

    @property
    def user_manager(self) -> UserManager:
        if self._user_manager is None:
            self._user_manager = UserManager(self.user_db)

        return self._user_manager


class ContainerGetter(Protocol):
    def __call__(
        self, request: Request | None = None
    ) -> AbstractAsyncContextManager[ServiceContainer]:
        raise NotImplementedError
