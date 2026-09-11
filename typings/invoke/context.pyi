from collections.abc import Generator, Mapping
from contextlib import contextmanager
from os import PathLike
from typing import Literal, TextIO, TypedDict, Unpack

from invoke.config import Config, DataProxy
from invoke.runners import Result
from invoke.watchers import StreamWatcher

type _Hide = (
    Literal[True, False, "out", "stdout", "err", "stderr", "both"] | None
)

class _RunKwargs(TypedDict, total=False):
    asynchronous: bool
    disown: bool
    dry: bool
    echo: bool
    echo_format: str | None
    echo_stdin: bool | None
    encoding: str | None
    err_stream: TextIO | None
    env: Mapping[str, str] | None
    fallback: bool
    hide: _Hide
    in_stream: TextIO | bool | None
    out_stream: TextIO | None
    pty: bool
    replace_env: bool
    shell: str
    timeout: float | None
    warn: bool
    watchers: list[StreamWatcher]

class Context(DataProxy):
    def __init__(self, config: Config | None = ...) -> None: ...
    @property
    def config(self) -> Config: ...
    @config.setter
    def config(self, value: Config) -> None: ...
    def run(
        self, command: str, **kwargs: Unpack[_RunKwargs]
    ) -> Result | None: ...
    def sudo(
        self,
        command: str,
        *,
        password: str = ...,
        user: str = ...,
        **kwargs: Unpack[_RunKwargs],
    ) -> Result | None: ...
    @contextmanager
    def prefix(self, command: str) -> Generator[None]: ...
    @property
    def cwd(self) -> str: ...
    @contextmanager
    def cd(self, path: PathLike[str] | str) -> Generator[None]: ...

class MockContext(Context):
    def __init__(
        self, config: Config | None = ..., **kwargs: object
    ) -> None: ...
    def run(self, command: str, *args: object, **kwargs: object) -> Result: ...
    def sudo(
        self, command: str, *args: object, **kwargs: object
    ) -> Result: ...
    def set_result_for(
        self, attname: str, command: str, result: Result
    ) -> None: ...
