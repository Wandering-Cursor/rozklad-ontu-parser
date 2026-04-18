class BaseError(Exception):
    pass


class ValueExpiredError(ValueError, BaseError):
    def __init__(self, value: object, message: str = "Value is expired") -> None:
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
    ) -> None:
        self.status_code = status_code
        self.response_content = response_content
        super().__init__(
            {
                "msg": message,
                "status_code": status_code,
                "response_content": response_content,
            }
        )


class ParsingError(BaseError):
    def __init__(
        self,
        message: str,
        content: str | None = None,
        underlying_error: Exception | None = None,
    ) -> None:
        self.content = content
        self.underlying_error = underlying_error

        super().__init__(
            {
                "msg": message,
                "content": content,
                "underlying_error": underlying_error,
            }
        )


ParingError = ParsingError  # Compatibility alias, will be deprecated in 1.1.0
