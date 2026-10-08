import logging

from fastapi_problem.handler import new_exception_handler
from rfc9457 import NotFoundProblem

from . import cors_configuration

logger = logging.getLogger(__name__)

error_handler = new_exception_handler(logger=logger, cors=cors_configuration)


class ProjectNotFoundError(NotFoundProblem):
    type_ = "project-not-found"
    title = (
        "Architectural project with specified id hasn't been found in database"
    )


class ItemNotFoundError(NotFoundProblem):
    type_ = "specification-item-not-found"
    title = (
        "Specification item with specified id hasn't been found in database"
    )
