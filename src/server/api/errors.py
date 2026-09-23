import logging

from rfc9457 import NotFoundProblem

logger = logging.getLogger(__name__)


class SpecificationNotFoundError(NotFoundProblem):
    type_ = "specification-not-found"
    title = "Specification with specified id hasn't been found in database"
