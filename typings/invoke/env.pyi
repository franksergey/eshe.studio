from typing import Any

from invoke.config import Config

class Environment:
    def __init__(self, config: Config, prefix: str) -> None: ...
    def load(self) -> dict[str, Any]: ...
