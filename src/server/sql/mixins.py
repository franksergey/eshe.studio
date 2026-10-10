from datetime import UTC, datetime
from typing import override

from sqlalchemy import DateTime, Dialect, func, types
from sqlalchemy.orm import Mapped, declarative_mixin, mapped_column


class UTCDateTime(types.TypeDecorator[datetime]):
    """
    A SQLAlchemy type that guarantees timezone-aware datetimes are stored
    and returned in UTC, preventing naive datetimes from entering the database.
    """

    impl = DateTime(timezone=True)
    cache_ok = True

    @override
    def process_bind_param(
        self, value: object, dialect: Dialect
    ) -> datetime | None:
        if value is None:
            return value

        if not isinstance(value, datetime):
            msg = "Expected datetime object"
            raise TypeError(msg)

        # Prevent naive datetimes from being saved
        if value.tzinfo is None:
            msg = (
                f"Naive datetime {value!r} is not allowed. "
                "Provide a TZ-aware datetime."
            )
            raise ValueError(msg)

        # Normalize to UTC before saving
        return value.astimezone(UTC)

    @override
    def process_result_value(
        self, value: object, dialect: Dialect
    ) -> datetime | None:
        if value is None:
            return value

        if not isinstance(value, datetime):
            msg = "Expected datetime object"
            raise TypeError(msg)

        # Databases like SQLite/MySQL return naive datetimes;
        # if so, explicitly assert/attach UTC.
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)

        return value.astimezone(UTC)


@declarative_mixin
class CreatedAtMixin:
    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime, server_default=func.now()
    )


@declarative_mixin
class UpdatedAtMixin:
    updated_at: Mapped[datetime] = mapped_column(
        UTCDateTime, server_default=func.now(), onupdate=func.now()
    )


@declarative_mixin
class TimestampMixin(CreatedAtMixin, UpdatedAtMixin):
    pass
