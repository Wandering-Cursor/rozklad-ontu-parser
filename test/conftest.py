from collections.abc import AsyncGenerator, Generator

import pytest
import pytest_asyncio

from ontu_parser.dataclasses.cookies import Cookies
from ontu_parser.dataclasses.sender import SenderOptions
from ontu_parser.parser import AsyncParser, Parser
from ontu_parser.utils.request_sender import RequestSender


@pytest.fixture(scope="session")
def cookies() -> Cookies:
    sender = RequestSender(max_cookie_retries=5)

    if getattr(sender, "_cookies", None) is None:
        return sender.update_cookies()

    return sender._cookies  # noqa: SLF001


@pytest.fixture()
def regular_parser(cookies: Cookies) -> Generator[Parser, None, None]:
    parser = Parser(
        sender_options=SenderOptions(
            cookies=cookies.value,
            cookies_issued_at=cookies.issued_at,
            max_cookie_retries=5,
        )
    )
    try:
        yield parser
    finally:
        parser.sender.client.close()


@pytest.fixture()
def teacher_parser(cookies: Cookies) -> Generator[Parser, None, None]:
    parser = Parser(
        sender_options=SenderOptions(
            for_teachers=True,
            cookies=cookies.value,
            cookies_issued_at=cookies.issued_at,
            max_cookie_retries=5,
        )
    )
    try:
        yield parser
    finally:
        parser.sender.client.close()


@pytest_asyncio.fixture()
async def async_parser(cookies: Cookies) -> AsyncGenerator[AsyncParser, None]:
    parser = AsyncParser(
        sender_options=SenderOptions(
            cookies=cookies.value,
            cookies_issued_at=cookies.issued_at,
            max_cookie_retries=5,
        )
    )

    try:
        yield parser
    finally:
        await parser.sender.client.aclose()


@pytest_asyncio.fixture()
async def async_teacher_parser(cookies: Cookies) -> AsyncGenerator[AsyncParser, None]:
    parser = AsyncParser(
        sender_options=SenderOptions(
            for_teachers=True,
            cookies=cookies.value,
            cookies_issued_at=cookies.issued_at,
            max_cookie_retries=5,
        )
    )

    try:
        yield parser
    finally:
        await parser.sender.client.aclose()


@pytest.fixture()
def faculty_name() -> str:
    return "ННІКІАРтаП"


@pytest.fixture()
def it_faculty_group_prefix() -> str:
    return "КН-"  # noqa: RUF001


@pytest.fixture()
def second_faculty_name() -> str:
    return "ННІХКтаЕ"
