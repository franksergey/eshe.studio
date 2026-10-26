import asyncio
import hashlib
import logging
import os
import uuid
from dataclasses import dataclass
from typing import TYPE_CHECKING, BinaryIO, override

from sqlalchemy import select

from server.domain.files.ports import AbstractObjectStorage
from server.domain.files.schemas import ObjectInfo
from server.sql.models import BlobID, StorageObjectDB

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

    from sqlalchemy.ext.asyncio import AsyncSession

    from server.domain.files.schemas import ContentType, ObjectKey

logger = logging.getLogger(__name__)

CHUNK_SIZE = 512 * 1024


def _unlink_quiet(path: Path) -> None:
    try:
        path.unlink(missing_ok=True)
    except OSError:
        logger.exception("Failed to unlink %s (left for GC)", path)


def _unlink_paths(paths: Iterable[Path]) -> None:
    for path in paths:
        _unlink_quiet(path)


def _fsync_dir(path: Path) -> None:
    try:
        fd = os.open(path, os.O_RDONLY)
    except OSError:
        return

    try:
        os.fsync(fd)
    except OSError:
        pass
    finally:
        os.close(fd)


def _stage_sync(content: BinaryIO, tmp_dir: Path) -> StagedBlob:
    tmp_dir.mkdir(parents=True, exist_ok=True)
    path = tmp_dir / uuid.uuid4().hex
    digest = hashlib.sha256()
    size = 0

    try:
        with path.open("wb") as f:
            while chunk := content.read(CHUNK_SIZE):
                f.write(chunk)
                digest.update(chunk)
                size += len(chunk)

            f.flush()
            os.fsync(f.fileno())
    except BaseException:
        _unlink_quiet(path)
        raise

    return StagedBlob(path=path, size=size, sha256=digest.hexdigest())


def _publish_sync(tmp: Path, final: Path) -> None:
    final.parent.mkdir(parents=True, exist_ok=True)
    tmp.replace(final)
    _fsync_dir(final.parent)


@dataclass(eq=False, slots=True, frozen=True)
class StagedBlob:
    def discard(self) -> None:
        _unlink_quiet(self.path)

    path: Path
    size: int
    sha256: str


@dataclass(eq=False, slots=True)
class LocalObjectsStorage(AbstractObjectStorage):
    session: AsyncSession
    storage: Path

    _blobs_dir: Path
    _staged_dir: Path

    _on_rollback: list[Path]
    _on_commit: list[Path]

    def __init__(self, session: AsyncSession, storage_dir: Path) -> None:
        self.session = session
        self.storage = storage_dir

        self._staged_dir = storage_dir / "staged"
        self._blobs_dir = storage_dir / "blobs"

        self._on_rollback = []
        self._on_commit = []

    def _blob_path(self, blob_id: BlobID) -> Path:
        blob = str(blob_id)

        return self._blobs_dir / blob[:2] / blob

    async def _stage(self, content: BinaryIO) -> StagedBlob:
        return await asyncio.to_thread(_stage_sync, content, self._staged_dir)

    async def _publish(self, staged: StagedBlob, blob_id: BlobID) -> None:
        final = self._blob_path(blob_id)

        self._on_rollback.append(final)
        await asyncio.to_thread(_publish_sync, staged.path, final)

    @staticmethod
    def _to_domain_schema(obj: StorageObjectDB) -> ObjectInfo:
        return ObjectInfo(
            id=obj.id,
            size=obj.size,
            sha256=obj.sha256,
            etag=obj.etag,
            original_filename=obj.original_filename,
            content_type=obj.content_type,
            created_at=obj.created_at,
            updated_at=obj.updated_at,
        )

    @override
    async def get(self, key: ObjectKey) -> Path | None:
        stmt = select(StorageObjectDB.blob_id).where(StorageObjectDB.id == key)
        blob_id = await self.session.scalar(stmt)

        return self._blob_path(blob_id) if blob_id is not None else None

    @override
    async def head(self, key: ObjectKey) -> ObjectInfo | None:
        obj = await self.session.get(StorageObjectDB, key)

        return self._to_domain_schema(obj) if obj is not None else None

    @override
    async def create(
        self,
        content: BinaryIO,
        filename: str | None = None,
        content_type: ContentType | None = None,
    ) -> ObjectInfo:
        staged = await self._stage(content)

        try:
            obj = StorageObjectDB(
                id=uuid.uuid4(),
                blob_id=uuid.uuid4(),
                size=staged.size,
                sha256=staged.sha256,
                etag=uuid.uuid4().hex,
                original_filename=filename,
                content_type=content_type,
            )
            self.session.add(obj)
            await self.session.flush((obj,))

            await self._publish(staged, obj.blob_id)
        except BaseException:
            staged.discard()
            raise

        return self._to_domain_schema(obj)

    async def _select_for_update(
        self, key: ObjectKey
    ) -> StorageObjectDB | None:
        stmt = (
            select(StorageObjectDB)
            .where(StorageObjectDB.id == key)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
        return await self.session.scalar(stmt)

    @override
    async def delete(self, key: ObjectKey) -> None:
        obj = await self._select_for_update(key)

        if obj is None:
            return

        blob_path = self._blob_path(obj.blob_id)
        await self.session.delete(obj)
        await self.session.flush((obj,))

        self._on_commit.append(blob_path)

    @override
    async def put(
        self,
        key: ObjectKey,
        content: BinaryIO,
        filename: str | None = None,
        content_type: ContentType | None = None,
        expected: ObjectInfo | None = None,
    ) -> ObjectInfo | None:
        obj = await self._select_for_update(key)

        if expected is not None and (obj is None or obj.etag != expected.etag):
            return None

        staged = await self._stage(content)

        try:
            if obj is None:
                obj = StorageObjectDB(id=key)
                self.session.add(obj)
            else:
                self._on_commit.append(self._blob_path(obj.blob_id))

            obj.blob_id = uuid.uuid4()
            obj.size = staged.size
            obj.sha256 = staged.sha256
            obj.etag = uuid.uuid4().hex
            obj.original_filename = filename
            obj.content_type = content_type

            await self.session.flush((obj,))
            await self._publish(staged, obj.blob_id)
        except BaseException:
            await asyncio.to_thread(staged.discard)
            raise

        return self._to_domain_schema(obj)

    async def confirm(self) -> None:
        self._on_rollback.clear()
        await asyncio.shield(asyncio.to_thread(_unlink_paths, self._on_commit))

    async def rollback(self) -> None:
        self._on_commit.clear()
        await asyncio.shield(
            asyncio.to_thread(_unlink_paths, self._on_rollback)
        )

    def forget(self) -> None:
        self._on_commit.clear()
        self._on_rollback.clear()
