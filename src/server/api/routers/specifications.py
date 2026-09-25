from fastapi import APIRouter

from server.api.dependencies import ContainerDependency
from server.api.errors import SpecificationNotFoundError, error_handler
from server.services.schemas import Specification, SpecificationPure

router = APIRouter(prefix="/specifications", tags=["Rooms Specifications"])


@router.get("/")
async def read_specifications(
    container: ContainerDependency,
) -> list[SpecificationPure]:
    """Получить список сразу всех комплектаций проектов."""
    return await container.specifications.get_all_pure()


@router.get(
    "/{id}",
    responses={
        404: error_handler.generate_swagger_response(
            SpecificationNotFoundError
        )
    },
)
async def read_specification(
    id: int, container: ContainerDependency
) -> Specification:
    """Получить список сразу всех комплектаций проектов."""
    return await container.specifications.get(id)
