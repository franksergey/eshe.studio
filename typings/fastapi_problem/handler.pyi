import logging
from typing import Any

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi_problem.cors import CorsConfiguration
from fastapi_problem.error import Problem, StatusProblem
from starlette.requests import Request
from starlette_problem.handler import (
    CorsPostHook,
    Handler,
    PostHook,
    PreHook,
    StripExtrasPostHook,
    http_exception_handler_,
)
from starlette_problem.handler import ExceptionHandler as BaseExceptionHandler

class ExceptionHandler(BaseExceptionHandler):
    def generate_swagger_response(
        self, *exceptions: type[Problem] | Problem
    ) -> dict[str, Any]: ...

def request_validation_handler_(
    eh: ExceptionHandler, _request: Request, exc: RequestValidationError
) -> Problem: ...
def new_exception_handler(
    logger: logging.Logger | None = None,
    cors: CorsConfiguration | None = None,
    unhandled_wrappers: dict[str, type[StatusProblem]] | None = None,
    handlers: dict[type[Exception], Handler] | None = None,
    pre_hooks: list[PreHook] | None = None,
    post_hooks: list[PostHook] | None = None,
    documentation_uri_template: str = "",
    http_exception_handler: Handler = ...,
    request_validation_handler: Handler = ...,
    *,
    strict_rfc9457: bool = False,
) -> ExceptionHandler: ...
def add_exception_handler(
    app: FastAPI,
    eh: ExceptionHandler | None = None,
    *,
    logger: logging.Logger | None = None,
    cors: CorsConfiguration | None = None,
    unhandled_wrappers: dict[str, type[StatusProblem]] | None = None,
    handlers: dict[type[Exception], Handler] | None = None,
    pre_hooks: list[PreHook] | None = None,
    post_hooks: list[PostHook] | None = None,
    documentation_uri_template: str = "",
    http_exception_handler: Handler = ...,
    request_validation_handler: Handler = ...,
    generic_swagger_defaults: bool = True,
    strict_rfc9457: bool = False,
) -> ExceptionHandler: ...

__all__ = [
    "CorsPostHook",
    "ExceptionHandler",
    "Handler",
    "PostHook",
    "PreHook",
    "StripExtrasPostHook",
    "add_exception_handler",
    "http_exception_handler_",
    "new_exception_handler",
    "request_validation_handler_",
]
