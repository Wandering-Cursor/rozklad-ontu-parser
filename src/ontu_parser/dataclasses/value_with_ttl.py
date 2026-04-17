import datetime
from typing import TypeVar

from ontu_parser.errors import ValueExpiredError

T = TypeVar("T")


class ValueWithTTL[T]:
    def __init__(
        self,
        value: T,
        ttl: datetime.timedelta | int = datetime.timedelta(hours=1),
        issued_at: datetime.datetime | None = None,
    ) -> None:
        self.ttl = ttl if isinstance(ttl, datetime.timedelta) else datetime.timedelta(seconds=ttl)

        self._value = value
        self.issued_at = issued_at or datetime.datetime.now(tz=datetime.UTC)

    @property
    def is_valid(self) -> bool:
        return datetime.datetime.now(tz=datetime.UTC) - self.issued_at < self.ttl

    @property
    def value(self) -> T:
        if self.is_valid:
            return self._value
        raise ValueExpiredError(self)

    def for_storage(self) -> tuple[datetime.datetime, T]:
        """Returns value in format suitable for storage (e.g. in database)"""
        return self.issued_at, self._value

    def __repr__(self) -> str:
        return f"ValueWithTTL(ttl={self.ttl}, issued_at={self.issued_at})"
