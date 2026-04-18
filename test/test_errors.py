import datetime
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import HTTPStatusError

from ontu_parser.dataclasses.sender import SenderOptions
from ontu_parser.errors import ParsingError
from ontu_parser.parser._async import AsyncParser
from test.common import async_skip_on_break


@pytest_asyncio.fixture()
async def async_parser_with_invalid_cookies() -> AsyncGenerator[AsyncParser, None]:
    parser = AsyncParser(
        sender_options=SenderOptions(
            cookies={"invalid": "cookies"},
            cookies_issued_at=datetime.datetime.now(tz=datetime.UTC),
            max_cookie_retries=5,
        )
    )

    try:
        yield parser
    finally:
        await parser.sender.client.aclose()


@pytest.mark.asyncio
async def test_async_parser_with_invalid_cookies(
    async_parser: AsyncParser,
    async_parser_with_invalid_cookies: AsyncParser,
) -> None:
    # Using a "valid" parser to ensure that the test is not broken due to other reasons
    if await async_skip_on_break(async_parser):
        return

    with pytest.raises(ParsingError) as exc_info:
        await async_parser_with_invalid_cookies.get_faculties()

    error = exc_info.value
    assert isinstance(error.underlying_error, HTTPStatusError)
    assert error.underlying_error.response.status_code == 503  # noqa: PLR2004
