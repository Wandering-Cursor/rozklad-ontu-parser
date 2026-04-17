import pytest

from ontu_parser.parser import Parser, AsyncParser


def skip_on_break(parser: Parser) -> bool:
    if parser.is_on_break():
        pytest.skip("rozklad.ontu.edu.ua system is on break")
        return True
    return False


@pytest.mark.asyncio
async def async_skip_on_break(parser: AsyncParser) -> bool:
    if await parser.is_on_break():
        pytest.skip("rozklad.ontu.edu.ua system is on break")
        return True
    return False
