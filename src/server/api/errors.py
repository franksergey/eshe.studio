import logging

from fastapi_problem.handler import new_exception_handler
from rfc9457 import ConflictProblem, NotFoundProblem, UnprocessableProblem

from .common import cors_configuration

logger = logging.getLogger(__name__)

error_handler = new_exception_handler(logger=logger, cors=cors_configuration)


class ProjectNotFoundError(NotFoundProblem):
    type_ = "project-not-found"
    title = "Architectural project with specified id hasn't been found."


class GroupNotFoundError(NotFoundProblem):
    type_ = "group-not-found"
    title = "Group with the specified index hasn't been found."


class ItemNotFoundError(NotFoundProblem):
    type_ = "specification-item-not-found"
    title = "Specification item with specified id hasn't been found."


class UserAlreadyExistsError(ConflictProblem):
    type_ = "user-already-exists"
    title = (
        "New user cannot be created as there already exists one with the "
        "specified email."
    )


class UserNotFoundError(NotFoundProblem):
    type_ = "user-not-found"
    title = "User with the specified email couldn't be found."


# Here, the term 'selection' becomes ridiculous
class SelectionNotFoundError(NotFoundProblem):
    type_ = "seletion-not-found"
    title = "Selection with the specified id couldn't be found."


class ObjectNotFoundError(NotFoundProblem):
    type_ = "object-not-found"
    title = "Object (file) with the specified key couldn't be found."


class ImageNotFoundError(NotFoundProblem):
    type_ = "image-not-found"
    title = "Image with the specified id couldn't be found."


class InvalidImageError(UnprocessableProblem):
    type_ = "invalid-image"
    title = "Uploaded image is invalid and could not be processed."


class InvalidTooLargeError(UnprocessableProblem):
    type_ = "image-too-large"
    title = "Uploaded image's dimensions are too large.."
