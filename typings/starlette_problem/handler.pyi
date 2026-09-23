import logging
import typing as t

from starlette.applications import Starlette
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette_problem.cors import CorsConfiguration
from starlette_problem.error import Problem, StatusProblem

type Handler = t.Callable[[ExceptionHandler, Request, Exception], Problem]
type PreHook = t.Callable[[Request, Exception], None]
type PostHook = t.Callable[
    [dict[str, t.Any], Request, Response], tuple[dict[str, t.Any], Response]
]

def http_exception_handler_(
    eh: ExceptionHandler, _request: Request, exc: HTTPException
) -> Problem: ...

class ExceptionHandler:
    def __init__(
        self: t.Self,
        logger: logging.Logger | None = ...,
        unhandled_wrappers: dict[str, type[StatusProblem]] | None = ...,
        handlers: dict[type[Exception], Handler] | None = ...,
        pre_hooks: list[PreHook] | None = ...,
        post_hooks: list[PostHook] | None = ...,
        documentation_uri_template: str = ...,
        *,
        strict_rfc9457: bool = ...,
    ) -> None: ...
    def __call__(
        self: t.Self, request: Request, exc: Exception
    ) -> Response: ...

class CorsPostHook:
    def __init__(self: t.Self, config: CorsConfiguration) -> None: ...
    def __call__(
        self: t.Self,
        content: dict[str, t.Any],
        request: Request,
        response: Response,
    ) -> tuple[dict[str, t.Any], Response]: ...

class StripExtrasPostHook:
    def __init__(
        self: t.Self,
        logger: logging.Logger | None = ...,
        mandatory_fields: list[str] | None = ...,
        exclude_status_codes: list[int] | None = ...,
        include_status_codes: list[int] | None = ...,
        *,
        enabled: bool = ...,
    ) -> None: ...
    def __call__(
        self: t.Self,
        content: dict[str, t.Any],
        _request: Request,
        response: JSONResponse,
    ) -> tuple[dict[str, t.Any], JSONResponse]: ...

def add_exception_handler(
    app: Starlette,
    logger: logging.Logger | None = ...,
    cors: CorsConfiguration | None = ...,
    unhandled_wrappers: dict[str, type[StatusProblem]] | None = ...,
    handlers: dict[type[Exception], Handler] | None = ...,
    pre_hooks: list[PreHook] | None = ...,
    post_hooks: list[PostHook] | None = ...,
    documentation_uri_template: str = ...,
    http_exception_handler: Handler = ...,
    *,
    strict_rfc9457: bool = ...,
) -> ExceptionHandler: ...
