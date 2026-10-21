import asyncio
import tempfile
from pathlib import Path
from typing import IO, TYPE_CHECKING, BinaryIO

import pyvips

from server.api.errors import InvalidImageError, InvalidTooLargeError

from .ports import AbstractImagesProcessor

if TYPE_CHECKING:
    from io import BufferedReader
    from types import TracebackType

MAX_PIXELS = 100_000_000


class ImagesProcessor(AbstractImagesProcessor):
    _tmp_files: list[IO[bytes]]
    _opened_files: list[BufferedReader]

    def __init__(self) -> None:
        self._tmp_files = []
        self._opened_files = []

    def cleanup(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        for file in self._opened_files:
            file.close()

        for tmp_file in self._tmp_files:
            tmp_file.__exit__(exc_type, exc, traceback)

    def _make_source(self, image: BinaryIO) -> pyvips.SourceCustom:
        source = pyvips.SourceCustom()
        source.on_read(image.read)
        source.on_seek(image.seek)

        return source

    def _get_tmp_file(self) -> Path:
        tmp_file = tempfile.NamedTemporaryFile(  # noqa: SIM115
            "rb", suffix=".webp", delete=True
        )
        self._tmp_files.append(tmp_file)

        return Path(tmp_file.__enter__().name)

    def _open_file(self, path: Path) -> BinaryIO:
        file = path.open("rb")
        self._opened_files.append(file)

        return file

    async def compress(
        self, image: BinaryIO, size: tuple[int, int], quality: int
    ) -> BinaryIO:
        target_w, target_h = size

        try:
            return await asyncio.to_thread(
                self._compress_sync, image, target_w, target_h, quality
            )
        except pyvips.Error as e:
            raise InvalidImageError from e

    def _compress_sync(
        self, image: BinaryIO, width: int, height: int, quality: int
    ) -> BinaryIO:
        header = pyvips.Image.new_from_source(
            self._make_source(image), "", access="sequential"
        ).autorot()

        if header.width * header.height > MAX_PIXELS:
            raise InvalidTooLargeError

        img = pyvips.Image.thumbnail_source(
            self._make_source(image),
            width,
            height=height,
            size="both",
            crop="centre",
            output_profile="srgb",
        )
        dst = self._get_tmp_file()
        img.write_to_file(dst, Q=quality, strip=True, effort=4)

        return self._open_file(dst)
