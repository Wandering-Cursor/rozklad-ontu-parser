import datetime

from ontu_parser.dataclasses.base import BaseSchema


class SenderOptions(BaseSchema):
    """Options for Sender class"""

    api_url: str = "https://rozklad.ontu.edu.ua"
    for_teachers: bool = False
    cookies: dict[str, str] | None = None
    cookies_issued_at: datetime.datetime | None = None
    max_cookie_retries: int = 3
