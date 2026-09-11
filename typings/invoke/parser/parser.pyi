from collections.abc import Iterable
from typing import Any

from invoke.parser.context import ParserContext

def is_flag(value: str) -> bool: ...
def is_long_flag(value: str) -> bool: ...

class ParseResult(list[ParserContext]):
    def __init__(self, *args: Any, **kwargs: Any) -> None: ...  # noqa: ANN401

class Parser:
    def __init__(
        self,
        contexts: Iterable[ParserContext] = ...,
        initial: ParserContext | None = ...,
        ignore_unknown: bool = ...,
    ) -> None: ...
    def parse_argv(self, argv: list[str]) -> ParseResult: ...
