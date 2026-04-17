import asyncio
import datetime
import time
from collections.abc import Mapping
from typing import Literal, TypeVar

import httpx
import pydantic
from httpx._status_codes import codes
from httpx._types import AuthTypes, RequestContent, RequestData, RequestFiles

from ontu_parser.dataclasses import Cookies
from ontu_parser.errors import RequestError, ValueExpiredError
from ontu_parser.settings import instance
from ontu_parser.utils.logging import request_logger
from ontu_parser.utils.waf_solver import JavaScriptParser

T = TypeVar("T")


class BaseRequestSender:
    def __init__(
        self,
        api_url: pydantic.HttpUrl | str = instance.api_url,
        *,
        for_teachers: bool = False,
        cookies: dict[str, str] | None = None,
        cookies_issued_at: datetime.datetime | None = None,
    ) -> None:
        if isinstance(api_url, str):
            api_url = pydantic.HttpUrl(api_url)
        self.api_url = api_url

        if cookies and cookies_issued_at:
            self._cookies = Cookies(
                value=cookies,
                issued_at=cookies_issued_at,
            )
        else:
            self._cookies: Cookies = Cookies(
                value={},
                issued_at=datetime.datetime(
                    2000,
                    1,
                    1,
                    tzinfo=datetime.UTC,
                ),
            )

        self._for_teachers = for_teachers

    @classmethod
    def headers(cls) -> dict[str, str]:
        return {
            "User-Agent": f"makisukurisu/rozklad-ontu-parser; (ontu_schedule_bot-{cls.__name__})",
        }

    @classmethod
    def guest_page(cls) -> str:
        """Used for general requests"""
        return "/guest_n.php"

    @classmethod
    def teachers_page(cls) -> str:
        """Used for requests related to teachers"""
        return "/departments_all.php"


class RequestSender(BaseRequestSender):
    def __init__(
        self,
        api_url: pydantic.HttpUrl | str = instance.api_url,
        *,
        for_teachers: bool = False,
        cookies: dict[str, str] | None = None,
        cookies_issued_at: datetime.datetime | None = None,
    ) -> None:
        super().__init__(
            api_url=api_url,
            for_teachers=for_teachers,
            cookies=cookies,
            cookies_issued_at=cookies_issued_at,
        )

        self.client = httpx.Client(base_url=str(self.api_url), timeout=30, headers=self.headers())

        if not self._cookies.is_valid:
            self._cookies: Cookies = self.update_cookies()

    def update_cookies(self) -> Cookies:
        request_logger.info("Fetching cookies")

        response = None
        retries = 3

        response = self.send_request(
            method="GET",
            endpoint="",
            ignore_own_cookies=True,
        )

        if response.status_code == codes.OK:
            return Cookies(
                value=dict(response.cookies),
                issued_at=datetime.datetime.now(tz=datetime.UTC),
            )

        cookies = JavaScriptParser(
            html=response.text,
        ).parse()

        for i in range(retries):
            session_response = self.send_request(
                method="GET",
                endpoint="",
                cookies=cookies,
                ignore_own_cookies=True,
            )

            php_session_id = session_response.cookies.get("PHPSESSID")

            if php_session_id is None:
                retry_after = (i + 1) ** 2
                request_logger.warning(
                    f"Attempt {i + 1}: Could not get cookies. Retrying in {retry_after} seconds.",
                )
                time.sleep(retry_after)
                continue

            return Cookies(
                value={
                    "PHPSESSID": php_session_id,
                    **cookies.value,
                },
                issued_at=datetime.datetime.now(tz=datetime.UTC),
            )

        raise RequestError(
            message=f"Could not get cookies after {retries} attempts",
            status_code=response.status_code if response else None,
            response_content=response.content if response else None,
        )

    def send_request(  # noqa: PLR0913
        self,
        method: Literal["GET", "POST", "PUT", "DELETE", "PATCH"],
        endpoint: str | None = None,
        content: RequestContent | None = None,
        data: RequestData | None = None,
        files: RequestFiles | None = None,
        json: object | None = None,
        params: Mapping[str, str | int | float | bool] | None = None,
        headers: dict[str, str] | None = None,
        cookies: Cookies | dict[str, str] | None = None,
        auth: AuthTypes | None = None,
        timeout: float | None = None,
        *,
        refetch_cookies_on_expiry: bool = True,
        ignore_own_cookies: bool = False,
    ) -> httpx.Response:
        request_logger.info(f"Sending {method} request to {endpoint}")

        if endpoint is None:
            endpoint = self.teachers_page() if self._for_teachers else self.guest_page()

        headers = {**(headers or {}), **self.headers()}

        if isinstance(cookies, Cookies):
            # not trying to refetch, since these cookies were
            # explicitly passed by the user, so they should know if they are expired or not
            cookies = cookies.value

        if ignore_own_cookies:
            cookies = cookies or {}
        else:
            try:
                cookies = {**(cookies or {}), **self._cookies.value}
            except ValueExpiredError:
                if not refetch_cookies_on_expiry:
                    raise

                request_logger.info("Cookies expired, refetching")
                self._cookies = self.update_cookies()
                cookies = {**(cookies or {}), **self._cookies.value}

        self.client.cookies = cookies

        response = self.client.request(
            method=method,
            url=endpoint,
            content=content,
            data=data,
            files=files,
            json=json,
            params=params,
            headers=headers,
            auth=auth,
            timeout=timeout,
        )

        request_logger.info(f"Received response with status code {response.status_code}")

        return response


class AsyncRequestSender(BaseRequestSender):
    def __init__(
        self,
        api_url: pydantic.HttpUrl | str = instance.api_url,
        *,
        for_teachers: bool = False,
        cookies: dict[str, str] | None = None,
        cookies_issued_at: datetime.datetime | None = None,
    ) -> None:
        super().__init__(
            api_url=api_url,
            for_teachers=for_teachers,
            cookies=cookies,
            cookies_issued_at=cookies_issued_at,
        )

        self.client = httpx.AsyncClient(
            base_url=str(self.api_url),
            timeout=30,
            headers=self.headers(),
        )

    async def update_cookies(self) -> Cookies:
        request_logger.info("Fetching cookies")

        response = None
        retries = 3

        response = await self.send_request(
            method="GET",
            endpoint="",
            ignore_own_cookies=True,
        )

        if response.status_code == codes.OK:
            return Cookies(
                value=dict(response.cookies),
                issued_at=datetime.datetime.now(tz=datetime.UTC),
            )

        cookies = await JavaScriptParser(
            html=response.text,
        ).async_parse()

        for i in range(retries):
            session_response = await self.send_request(
                method="GET",
                endpoint="",
                cookies=cookies,
                ignore_own_cookies=True,
            )

            php_session_id = session_response.cookies.get("PHPSESSID")

            if php_session_id is None:
                retry_after = (i + 1) ** 2
                request_logger.warning(
                    f"Attempt {i + 1}: Could not get cookies. Retrying in {retry_after} seconds.",
                )
                await asyncio.sleep(retry_after)
                continue

            return Cookies(
                value={
                    "PHPSESSID": php_session_id,
                    **cookies.value,
                },
                issued_at=datetime.datetime.now(tz=datetime.UTC),
            )

        raise RequestError(
            message=f"Could not get cookies after {retries} attempts",
            status_code=response.status_code if response else None,
            response_content=response.content if response else None,
        )

    async def send_request(  # noqa: PLR0913
        self,
        method: Literal["GET", "POST", "PUT", "DELETE", "PATCH"],
        endpoint: str | None = None,
        content: RequestContent | None = None,
        data: RequestData | None = None,
        files: RequestFiles | None = None,
        json: object | None = None,
        params: Mapping[str, str | int | float | bool] | None = None,
        headers: dict[str, str] | None = None,
        cookies: Cookies | dict[str, str] | None = None,
        auth: AuthTypes | None = None,
        timeout: float | None = None,  # noqa: ASYNC109
        *,
        refetch_cookies_on_expiry: bool = True,
        ignore_own_cookies: bool = False,
    ) -> httpx.Response:
        request_logger.info(f"Sending {method} request to {endpoint}")

        if endpoint is None:
            endpoint = self.teachers_page() if self._for_teachers else self.guest_page()

        headers = {**(headers or {}), **self.headers()}

        if isinstance(cookies, Cookies):
            # not trying to refetch, since these cookies were
            # explicitly passed by the user, so they should know if they are expired or not
            cookies = cookies.value

        if ignore_own_cookies:
            cookies = cookies or {}
        else:
            try:
                cookies = {**(cookies or {}), **self._cookies.value}
            except ValueExpiredError:
                if not refetch_cookies_on_expiry:
                    raise

                request_logger.info("Cookies expired, refetching")
                self._cookies = await self.update_cookies()
                cookies = {**(cookies or {}), **self._cookies.value}

        self.client.cookies = cookies

        response = await self.client.request(
            method=method,
            url=endpoint,
            content=content,
            data=data,
            files=files,
            json=json,
            params=params,
            headers=headers,
            auth=auth,
            timeout=timeout,
        )

        request_logger.info(f"Received response with status code {response.status_code}")

        return response
