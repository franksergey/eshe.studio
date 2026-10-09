from dataclasses import dataclass
from typing import TYPE_CHECKING

from server.domain.projects.service import ProjectsService
from server.sql.repos import ProjectsRepo

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


@dataclass(eq=False, slots=True)
class ServiceContainer:
    session: AsyncSession
    _specification_service: ProjectsService | None = None

    @property
    def specifications(self) -> ProjectsService:
        if self._specification_service is None:
            repo = ProjectsRepo(self.session)
            self._specification_service = ProjectsService(repo)

        return self._specification_service
