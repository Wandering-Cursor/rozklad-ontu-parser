from ontu_parser.utils.request_sender import ValueWithTTL


class BaseError(Exception):
    pass


class ValueExpiredError(ValueError, BaseError):
    def __init__(self, value: ValueWithTTL, message="Value is expired"):
        self.value = value
        super().__init__(
            {
                "msg": message,
                "value": value,
            }
        )


class RequestError(BaseError):
    def __init__(
        self,
        message: str,
        status_code: int | None,
        response_content: bytes | None,
    ):
        self.status_code = status_code
        self.response_content = response_content
        super().__init__(
            {
                "msg": message,
                "status_code": status_code,
                "response_content": response_content,
            }
        )


class ParingError(BaseError):
    def __init__(self, message: str, content: str | None = None):
        self.content = content
        super().__init__(
            {
                "msg": message,
                "content": content,
            }
        )
