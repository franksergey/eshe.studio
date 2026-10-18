import asyncio
from email.utils import parsedate_to_datetime
from typing import TYPE_CHECKING

from fastapi import APIRouter, Request, Response
from fastapi.responses import FileResponse

from server.api.dependencies import ContainerDependency
from server.domain.files.schemas import ObjectKey

if TYPE_CHECKING:
    from starlette.datastructures import Headers

router = APIRouter(prefix="/storage")

NOT_MODIFIED_HEADERS = (
    "cache-control",
    "etag",
    "last-modified",
    "expires",
    "vary",
)


def is_not_modified(
    request_headers: Headers, etag: str | None, last_modified: str | None
) -> bool:
    # If-None-Match takes precedence over If-Modified-Since (RFC 9110)
    if_none_match = request_headers.get("if-none-match")

    if if_none_match is not None:
        if if_none_match.strip() == "*":
            return True

        tags = {t.strip().removeprefix("W/") for t in if_none_match.split(",")}
        return etag in tags

    if_modified_since = request_headers.get("if-modified-since")

    if if_modified_since and last_modified:
        try:
            return parsedate_to_datetime(
                last_modified
            ) <= parsedate_to_datetime(if_modified_since)
        except TypeError, ValueError:
            return False

    return False


@router.get("/{key}")
async def read_file(
    key: ObjectKey, request: Request, container: ContainerDependency
) -> FileResponse | Response:
    path = await container.files.get(key)
    response = FileResponse(
        path,
        # makes FileResponse compute ETag/Last-Modified now
        stat_result=await asyncio.to_thread(path.stat),
    )

    if is_not_modified(
        request.headers,
        response.headers.get("etag"),
        response.headers.get("last-modified"),
    ):
        return Response(
            status_code=304,
            headers={
                k: v
                for k, v in response.headers.items()
                if k in NOT_MODIFIED_HEADERS
            },
        )

    return response
