"""Package with all operational code of the static site's FastAPI backend."""

from importlib import metadata

__all__ = ["__version__"]
PACKAGE_NAME = "eshe-studio-site"

try:
    __version__ = metadata.version(PACKAGE_NAME)
except metadata.PackageNotFoundError:
    __version__ = "0.1.dev1+UNKNOWN"
