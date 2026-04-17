import pydantic
from pydantic_settings import BaseSettings, SettingsConfigDict

from ontu_parser.enums import LogLevel


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        env_prefix="ONTU_PARSER_",
        alias_generator=lambda s: s.upper(),
    )

    log_to_file: bool = False
    log_file_path: str = "ontu_parser.log"
    log_level: LogLevel = LogLevel.DEBUG
    request_log_level: LogLevel = LogLevel.INFO

    api_url: pydantic.HttpUrl = pydantic.HttpUrl("https://rozklad.ontu.edu.ua")


instance = Settings()
