import logging

import pytest

from ontu_parser.dataclasses.faculty import Faculty
from ontu_parser.parser._async import AsyncParser
from test.common import async_skip_on_break


@pytest.mark.asyncio
async def test_faculties(async_parser: AsyncParser, faculty_name: str) -> None:
    if await async_skip_on_break(async_parser):
        return

    faculties = await async_parser.get_faculties()

    assert len(faculties) > 0

    it_faculty = next(filter(lambda f: f.faculty_name == faculty_name, faculties), None)
    assert it_faculty is not None, f"{faculty_name} faculty not found"


async def get_faculty_by_name(async_parser: AsyncParser, faculty_name: str) -> Faculty:
    faculties = await async_parser.get_faculties()

    it_faculty = next(filter(lambda f: f.faculty_name == faculty_name, faculties), None)

    assert it_faculty is not None, f"{faculty_name} faculty not found from faculties list"

    return it_faculty


@pytest.mark.asyncio
async def test_get_faculty(async_parser: AsyncParser, faculty_name: str) -> None:
    if await async_skip_on_break(async_parser):
        return

    it_faculty = await get_faculty_by_name(async_parser, faculty_name)

    faculty = await async_parser.get_faculty(it_faculty.faculty_id)

    assert faculty is not None, f"{faculty_name} faculty not found"


@pytest.mark.asyncio
async def test_get_extramural(
    async_parser: AsyncParser,
    faculty_name: str,
    second_faculty_name: str,
) -> None:
    if await async_skip_on_break(async_parser):
        return

    it_faculty = await get_faculty_by_name(async_parser, faculty_name)

    it_extramural = await async_parser.get_extramural(it_faculty)

    assert it_extramural is not None, f"{faculty_name} extramural faculty not found"

    second_faculty = await get_faculty_by_name(async_parser, second_faculty_name)

    second_extramural = await async_parser.get_extramural(second_faculty)

    assert second_extramural is not None, (
        f"{second_faculty_name} extramural faculty should not be found"
    )
    assert second_extramural != it_extramural, (
        f"{second_faculty_name} extramural faculty should not be the same as {faculty_name} extramural faculty"  # noqa: E501
    )


@pytest.mark.asyncio
async def test_get_groups(
    async_parser: AsyncParser,
    faculty_name: str,
    it_faculty_group_prefix: str,
) -> None:
    if await async_skip_on_break(async_parser):
        return

    it_faculty = await get_faculty_by_name(async_parser, faculty_name)

    groups = await async_parser.get_groups(faculty=it_faculty)

    assert len(groups) > 0, f"{faculty_name} groups not found"

    kn_group = next(
        filter(
            lambda g: (g.group_name or "").startswith(it_faculty_group_prefix),
            groups,
        ),
        None,
    )

    assert kn_group is not None, (
        f"{faculty_name} group with {it_faculty_group_prefix} prefix not found"
    )


@pytest.mark.asyncio
async def test_get_extramural_groups(
    async_parser: AsyncParser,
    faculty_name: str,
    it_faculty_group_prefix: str,
) -> None:
    if await async_skip_on_break(async_parser):
        return

    it_faculty = await get_faculty_by_name(async_parser, faculty_name)

    extramural = await async_parser.get_extramural(it_faculty)

    assert extramural is not None, f"{faculty_name} extramural faculty not found"

    groups = await async_parser.get_groups(faculty=extramural)

    assert len(groups) > 0, f"{faculty_name} extramural groups not found"

    kn_group = next(
        filter(
            lambda g: (g.group_name or "").startswith(it_faculty_group_prefix),
            groups,
        ),
        None,
    )

    if not kn_group:
        logging.warning(
            f"{faculty_name} extramural group with {it_faculty_group_prefix} prefix not found\n"
            "Ignoring for extramurals, since they can have different group names."
        )


@pytest.mark.asyncio
async def test_get_all_extramurals(
    async_parser: AsyncParser,
) -> None:
    if await async_skip_on_break(async_parser):
        return

    extramurals = await async_parser.get_all_extramurals()

    assert len(extramurals) > 0, "Extramural faculties not found"

    assert extramurals[0].parent_id != extramurals[1].parent_id, (
        "Extramural faculties should have different parent ids"
    )
    assert extramurals[0].prefix != extramurals[1].prefix, (
        "Extramural faculties should have different prefixes"
    )
    assert "Заочне навчання" in extramurals[0].faculty_name, (
        "Extramural faculty name should contain 'Заочне навчання'"
    )
