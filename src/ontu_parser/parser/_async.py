from bs4 import BeautifulSoup
from httpx import HTTPStatusError, Response

from ontu_parser.dataclasses import (
    Department,
    Faculty,
    Group,
    StudentsSchedule,
    Teacher,
    TeacherSchedule,
)
from ontu_parser.dataclasses.base import BaseClass
from ontu_parser.dataclasses.pair import StudentsPair, TeachersPair
from ontu_parser.dataclasses.sender import SenderOptions
from ontu_parser.errors import ParsingError
from ontu_parser.utils.request_sender import AsyncRequestSender


class AsyncParser(BaseClass):
    """Parser class to get information from Rozklad ONTU"""

    def __init__(
        self,
        sender_options: SenderOptions | None = None,
    ) -> None:
        self.for_teachers = sender_options.for_teachers if sender_options else False

        if sender_options:
            self.sender = AsyncRequestSender(
                api_url=sender_options.api_url,
                for_teachers=sender_options.for_teachers,
                cookies=sender_options.cookies,
                cookies_issued_at=sender_options.cookies_issued_at,
                max_cookie_retries=sender_options.max_cookie_retries,
            )
        else:
            self.sender = AsyncRequestSender()

    def _get_page(self, response: Response) -> BeautifulSoup:
        try:
            response.raise_for_status()
        except HTTPStatusError as e:
            raise ParsingError(
                "Failed to get page!",
                content=str(response),
                underlying_error=e,
            ) from e

        content = response.content
        if not content:
            raise ParsingError("Response has no content!", content=str(response))
        decoded_content = content.decode("utf-8")

        return BeautifulSoup(decoded_content, "html.parser")

    async def is_on_break(self) -> bool:
        """
        A check to see if the schedule system is on break.
        During breaks, no schedules are available.

        Using two methods:
            - See if there's a text about being on break;
            - See if there are any faculties listed. (If not - probably on break)

        If either method indicates a break, returns True.
        """
        main_response = await self.sender.send_request(method="GET")
        main_page = self._get_page(main_response)

        is_on_break_text = False
        contents = main_page.find_all(
            attrs={"data-role": "panel"},
            recursive=True,
        )
        for content in contents:
            if "доступний після" in content.text.lower():
                is_on_break_text = True
                break

        has_faculties = main_page.find(attrs={"class": "fc"}) is not None

        return is_on_break_text or not has_faculties

    async def get_faculties(self) -> list[Faculty]:
        """Returns a list of faculties as Faculty objects"""
        faculties_response = await self.sender.send_request(method="GET")
        faculty_page = self._get_page(faculties_response)
        faculty_elements = faculty_page.find_all(attrs={"class": "fc"})

        return [Faculty.from_tag(tag=tag) for tag in faculty_elements]

    async def get_faculty(self, faculty_id: int) -> Faculty | None:
        """
        Returns a Faculty object for a given faculty ID. If the faculty is not found, returns None.
        """
        faculties = await self.get_faculties()
        for faculty in faculties:
            if faculty.faculty_id == faculty_id:
                return faculty
        return None

    async def get_faculty_details(self, faculty_id: int) -> BeautifulSoup:
        """
        Returns the raw BeautifulSoup object for a given faculty ID.
        Use this method if you need to get some specific information about the faculty that is not
        included in the Faculty dataclass.
        """
        faculty_data = await self.sender.send_request(
            method="GET",
            data={"facultyid": faculty_id},
        )

        return self._get_page(faculty_data)

    async def get_all_extramurals(self) -> list[Faculty]:
        """Returns a list of extramural pseudo-faculties as Faculty objects"""
        return list(
            filter(
                None,
                [await self.get_extramural(faculty) for faculty in await self.get_faculties()],
            )
        )

    async def get_extramural(self, faculty: Faculty) -> Faculty | None:
        """
        Returns extramural pseudo-faculty for a given faculty.
        Returns None if no extramural pseudo-faculty found.

        NOTE: It might be better to return a list of extramurals, and not just one faculty.
        As of now there are no cases of multiple extramurals, but it might change in the future.
        """
        faculty_page = await self.get_faculty_details(faculty_id=faculty.faculty_id)
        pseudofaculty_tag = faculty_page.find(attrs={"class": "fc"})

        if not pseudofaculty_tag:
            return None

        return Faculty.from_tag(
            tag=pseudofaculty_tag,
            prefix=f"{faculty.faculty_name} -",
            parent_id=faculty.faculty_id,
        )

    async def get_groups(
        self,
        faculty_id: int | str | None = None,
        parent_id: int | str | None = None,
        faculty: Faculty | None = None,
    ) -> list[Group]:
        """
        Returns Group list of a faculty by faculty id
        """
        if isinstance(faculty_id, str):
            faculty_id = int(faculty_id)

        xor = (faculty_id is not None) != (faculty is not None)
        if not xor:
            raise ValueError("Exactly one of faculty_id or faculty must be provided")

        search_faculty_id = faculty_id or (faculty.faculty_id if faculty else None)
        search_parent_id = parent_id or (faculty.parent_id if faculty else None)

        if not search_faculty_id:
            raise RuntimeError(
                "Faculty ID must be provided either directly or through the Faculty object"
            )

        if search_parent_id is not None:
            # This is necessary to ensure that
            # we get the correct faculty set up on the server side
            # and get appropriate groups in response
            await self.get_faculty_details(faculty_id=int(search_parent_id))

        groups_response = await self.sender.send_request(
            method="POST",
            data={"facultyid": search_faculty_id},
        )
        groups_page = self._get_page(groups_response)
        group_tags = groups_page.find_all(attrs={"class": "grp"})
        return [Group.from_tag(tag=tag) for tag in group_tags]

    async def get_schedule(
        self,
        group_id: int | None = None,
        teacher_id: int | None = None,
        *,
        all_time: bool = False,
    ) -> dict[str, list[TeachersPair | StudentsPair]]:
        """
        Returns schedule for group, or for teachers
        """
        if group_id:
            return (await self.get_group_schedule(group_id, all_time=all_time)).week
        if teacher_id:
            return (await self.get_teachers_schedule(teacher_id, all_time=all_time)).week
        raise ValueError("No group or teacher id provided!")

    async def get_group_schedule(
        self,
        group_id: int,
        *,
        all_time: bool = False,
    ) -> StudentsSchedule:
        request_data = {
            "groupid": group_id,
        }
        if all_time:
            request_data["show_all"] = 1

        schedule_response = await self.sender.send_request(
            method="POST",
            data=request_data,
        )
        schedule_page = self._get_page(schedule_response)

        breadcrumbs = schedule_page.find(attrs={"class": "breadcrumbs"})

        if not breadcrumbs:
            raise ParsingError(
                "Schedule page has no breadcrumbs! Can't determine faculty and group!",
                content=str(schedule_page),
            )

        group_breadcrumbs = breadcrumbs.find_all(attrs={"class": "page-link"})

        table = schedule_page.find(attrs={"class": "table"})

        if not table:
            raise ParsingError(
                "Schedule page has no schedule table! Can't parse schedule!",
                content=str(schedule_page),
            )

        group_name = group_breadcrumbs[-1].text
        # I hate this, but at the same time - I love it
        # If it ever to become broken I'll implement this a bit thoughtfully :)
        subgroup_name = group_name.split("[")[1].replace("]", "")
        return StudentsSchedule.from_tag(table, subgroup=subgroup_name)

    def _check_for_teachers(self) -> None:
        if not self.for_teachers:
            raise ValueError(
                "This parser instance is not configured for teachers!\n"
                "Please create a new instance with appropriate SenderOptions."
            )

    async def get_teachers_schedule(
        self,
        teacher_id: int,
        *,
        all_time: bool = False,
    ) -> TeacherSchedule:
        self._check_for_teachers()

        request_data = {
            "page": "teacher",
            "teacher": teacher_id,
        }
        if all_time:
            request_data["page"] = "teacher_all"
            request_data["show"] = 1

        schedule_response = await self.sender.send_request(
            method="GET",
            params=request_data,
        )
        schedule_page = self._get_page(schedule_response)

        grid = schedule_page.find(name="div", attrs={"class": "grid"})
        if not grid:
            raise ParsingError(
                "Schedule page has no grid! Can't parse teacher's schedule!",
                content=str(schedule_page),
            )
        return TeacherSchedule.from_tag(grid)

    async def get_departments(self) -> list[Department]:
        """Returns a list of departments as Department objects"""
        self._check_for_teachers()

        departments_response = await self.sender.send_request(method="GET")
        departments_page = self._get_page(departments_response)

        tiles = departments_page.find(attrs={"class": "tiles-grid"})

        if not tiles:
            raise ParsingError("No tiles found!", content=str(departments_page))

        departments_tags = tiles.find_all(name="a", attrs={"data-role": "tile"})

        return [Department.from_tag(tag) for tag in departments_tags]

    async def get_teachers_by_department(
        self,
        department_id: int,
    ) -> list[Teacher]:
        """Returns a list of teachers for a given department ID"""
        self._check_for_teachers()

        teachers_response = await self.sender.send_request(
            method="GET",
            params={"page": "department", "dep": department_id},
        )
        teachers_page = self._get_page(teachers_response)

        teacher_tiles = teachers_page.find(attrs={"class": "tiles-grid"})
        if not teacher_tiles:
            raise ParsingError("No teachers found!", content=str(teachers_page))

        teacher_tiles = teacher_tiles.find_all(
            name="a",
            attrs={"data-role": "tile"},
        )

        return [Teacher.from_tag(tag) for tag in teacher_tiles]
