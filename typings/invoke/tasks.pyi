from collections.abc import Callable, Iterable
from inspect import Signature
from typing import Any, Self, overload

from invoke.config import Config
from invoke.context import Context
from invoke.parser import Argument

class Task[**P, R]:
    body: Callable[P, R]
    __doc__: str | None
    __name__: str
    __module__: str
    aliases: tuple[str, ...]
    is_default: bool
    positional: Iterable[str]
    optional: Iterable[str]
    iterable: Iterable[str]
    incrementable: Iterable[str]
    auto_shortflags: bool
    help: dict[str, str]
    pre: Iterable[Task[..., Any] | Call]
    post: Iterable[Task[..., Any] | Call]
    times_called: int
    autoprint: bool

    def __init__(
        self,
        body: Callable[P, R],
        name: str | None = ...,
        aliases: Iterable[str] = ...,
        positional: Iterable[str] | None = ...,
        optional: Iterable[str] = ...,
        default: bool = ...,
        auto_shortflags: bool = ...,
        help: dict[str, Any] | None = ...,  # noqa: A002
        pre: list[str] | str | None = ...,
        post: list[str] | str | None = ...,
        autoprint: bool = ...,
        iterable: Iterable[str] | None = ...,
        incrementable: Iterable[str] | None = ...,
    ) -> None: ...
    @property
    def name(self) -> str: ...
    def __eq__(self, other: object) -> bool: ...
    def __hash__(self) -> int: ...
    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R: ...
    @property
    def called(self) -> bool: ...
    def argspec(self, body: Callable[..., Any]) -> Signature: ...
    def fill_implicit_positionals(
        self, positional: Iterable[str] | None
    ) -> Iterable[str]: ...
    def arg_opts(
        self, name: str, default: str, taken_names: set[str]
    ) -> dict[str, Any]: ...
    def get_arguments(
        self, ignore_unknown_help: bool | None = ...
    ) -> list[Argument]: ...

@overload
def task[**P, R](
    *args: Task[..., Any] | Call,
    name: str | None = ...,
    aliases: tuple[str, ...] = ...,
    positional: Iterable[str] | None = ...,
    optional: Iterable[str] = ...,
    default: bool = ...,
    auto_shortflags: bool = ...,
    help: dict[str, str] | None = ...,
    pre: list[Task[..., Any] | Call] | None = ...,
    post: list[Task[..., Any] | Call] | None = ...,
    autoprint: bool = ...,
    iterable: Iterable[str] | None = ...,
    incrementable: Iterable[str] | None = ...,
) -> Callable[[Callable[P, R]], Task[P, R]]: ...
@overload
def task[TaskT](
    *args: Task[..., Any] | Call,
    name: str | None = ...,
    aliases: tuple[str, ...] = ...,
    positional: Iterable[str] | None = ...,
    optional: Iterable[str] = ...,
    default: bool = ...,
    auto_shortflags: bool = ...,
    help: dict[str, str] | None = ...,
    pre: list[Task[..., Any] | Call] | None = ...,
    post: list[Task[..., Any] | Call] | None = ...,
    autoprint: bool = ...,
    iterable: Iterable[str] | None = ...,
    incrementable: Iterable[str] | None = ...,
    klass: type[TaskT],
) -> Callable[[Callable[..., Any]], TaskT]: ...
@overload
def task[**P, R](func: Callable[P, R], /) -> Task[P, R]: ...

class Call:
    task: Task[..., Any]
    called_as: str | None
    args: tuple[Any, ...]
    kwargs: dict[str, Any]

    def __init__(
        self,
        task: Task[..., Any],
        called_as: str | None = ...,
        args: tuple[str, ...] | None = ...,
        kwargs: dict[str, Any] | None = ...,
    ) -> None: ...
    def __getattr__(self, name: str) -> Any: ...  # noqa: ANN401
    def __deepcopy__(self, memo: object) -> Self: ...
    def __eq__(self, other: object) -> bool: ...
    def make_context(self, config: Config) -> Context: ...
    def clone_data(self) -> dict[str, Any]: ...
    def clone(
        self, into: type[Call] | None = ..., with_: dict[str, Any] | None = ...
    ) -> Call: ...

def call[**P, R](
    task: Task[P, R], *args: object, **kwargs: object
) -> Call: ...
