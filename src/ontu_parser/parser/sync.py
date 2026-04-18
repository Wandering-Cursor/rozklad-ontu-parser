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
from ontu_parser.errors import ParingError
from ontu_parser.utils.request_sender import RequestSender


class Parser(BaseClass):
    """Parser class to get information from Rozklad ONTU"""

    def __init__(
        self,
        sender_options: SenderOptions | None = None,
    ) -> None:
        self.for_teachers = sender_options.for_teachers if sender_options else False

        if sender_options:
            self.sender = RequestSender(
                api_url=sender_options.api_url,
                for_teachers=sender_options.for_teachers,
                cookies=sender_options.cookies,
                cookies_issued_at=sender_options.cookies_issued_at,
                max_cookie_retries=sender_options.max_cookie_retries,
            )
        else:
            self.sender = RequestSender()

    def _get_page(self, response: Response) -> BeautifulSoup:
        try:
            response.raise_for_status()
        except HTTPStatusError as e:
            raise ParingError(
                "Failed to get page!",
                content=str(response),
                underlying_error=e,
            ) from e

        content = response.content
        if not content:
            raise ParingError("Response has no content!", content=str(response))
        decoded_content = content.decode("utf-8")

        return BeautifulSoup(decoded_content, "html.parser")

    def is_on_break(self) -> bool:
        """
        A check to see if the schedule system is on break.
        During breaks, no schedules are available.

        Using two methods:
            - See if there's a text about being on break;
            - See if there are any faculties listed. (If not - probably on break)

        If either method indicates a break, returns True.
        """
        main_response = self.sender.send_request(method="GET")
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

        has_faculties = len(main_page.find_all(attrs={"class": "fc"})) > 0

        return is_on_break_text or not has_faculties

    def get_faculties(self) -> list[Faculty]:
        """Returns a list of faculties as Faculty objects"""
        faculties_response = self.sender.send_request(method="GET")
        faculty_page = self._get_page(faculties_response)
        faculty_elements = faculty_page.find_all(attrs={"class": "fc"})

        return [Faculty.from_tag(tag=tag) for tag in faculty_elements]

    def get_faculty(self, faculty_id: int) -> Faculty | None:
        """
        Returns a Faculty object for a given faculty ID. If the faculty is not found, returns None.
        """
        faculties = self.get_faculties()
        for faculty in faculties:
            if faculty.faculty_id == faculty_id:
                return faculty
        return None

    def get_faculty_details(self, faculty_id: int) -> BeautifulSoup:
        """
        Returns the raw BeautifulSoup object for a given faculty ID.
        Use this method if you need to get some specific information about the faculty that is not
        included in the Faculty dataclass.
        """
        faculty_data = self.sender.send_request(
            method="GET",
            data={"facultyid": faculty_id},
        )

        return self._get_page(faculty_data)

    def get_all_extramurals(self) -> list[Faculty]:
        """Returns a list of extramural pseudo-faculties as Faculty objects"""
        return list(
            filter(
                None,
                [self.get_extramural(faculty) for faculty in self.get_faculties()],
            )
        )

    def get_extramural(self, faculty: Faculty) -> Faculty | None:
        """
        Returns extramural pseudo-faculty for a given faculty.
        Returns None if no extramural pseudo-faculty found.

        NOTE: It might be better to return a list of extramurals, and not just one faculty.
        As of now there are no cases of multiple extramurals, but it might change in the future.
        """
        faculty_page = self.get_faculty_details(faculty_id=faculty.faculty_id)
        pseudofaculty_tag = faculty_page.find(attrs={"class": "fc"})

        if not pseudofaculty_tag:
            return None

        return Faculty.from_tag(
            tag=pseudofaculty_tag,
            prefix=f"{faculty.faculty_name} -",
            parent_id=faculty.faculty_id,
        )

    def get_groups(
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
            self.get_faculty_details(faculty_id=int(search_parent_id))

        groups_response = self.sender.send_request(
            method="POST",
            data={"facultyid": search_faculty_id},
        )
        groups_page = self._get_page(groups_response)
        group_tags = groups_page.find_all(attrs={"class": "grp"})
        return [Group.from_tag(tag) for tag in group_tags]

    def get_schedule(
        self,
        group_id: int | None = None,
        teacher_id: int | None = None,
        *,
        all_time: bool = False,
    ) -> dict[str, list[TeachersPair | StudentsPair]]:
        """Returns schedule for group, or for teachers"""
        if group_id:
            return self.get_group_schedule(group_id, all_time=all_time).week
        if teacher_id:
            return self.get_teachers_schedule(teacher_id, all_time=all_time).week
        raise ValueError("No group or teacher id provided!")

    def get_group_schedule(
        self,
        group_id: int,
        *,
        all_time: bool = False,
    ) -> StudentsSchedule:
        """
        Returns a schedule for a group (by id)
        If all_time is False - returns schedule for current week
        Else - returns schedule for whole semester
        """
        request_data = {"groupid": group_id}
        if all_time:
            request_data["show_all"] = 1
        schedule_response = self.sender.send_request(
            method="POST",
            data=request_data,
        )
        schedule_page = self._get_page(schedule_response)

        breadcrumbs = schedule_page.find(attrs={"class": "breadcrumbs"})

        if not breadcrumbs:
            raise ParingError(
                "Schedule page has no breadcrumbs! Can't determine faculty and group!",
                content=str(schedule_page),
            )

        group_breadcrumbs = breadcrumbs.find_all(attrs={"class": "page-link"})

        table = schedule_page.find(attrs={"class": "table"})

        if not table:
            raise ParingError(
                "Schedule page has no schedule table! Can't parse schedule!",
                content=str(schedule_page),
            )

        group_name = group_breadcrumbs[-1].text
        # I hate this, but at the same time - I love it
        # If it ever to become broken I'll implement this a bit thoughtfully :)
        subgroup_name = group_name.split("[")[1].replace("]", "")
        return StudentsSchedule.from_tag(table, subgroup=subgroup_name)

    def get_teachers_schedule(
        self,
        teacher_id: int,
        *,
        all_time: bool = False,
    ) -> TeacherSchedule:
        """Returns a schedule for a teacher (by id)"""
        self._check_for_teachers()

        query = {
            "page": "teacher",
            "teacher": teacher_id,
        }
        if all_time:
            query["page"] = "teacher_all"
            query["show"] = 1

        schedule_response = self.sender.send_request(
            method="GET",
            params=query,
        )
        schedule_page = self._get_page(schedule_response)

        grid = schedule_page.find(name="div", attrs={"class": "grid"})
        if not grid:
            raise ParingError(
                "Schedule page has no grid! Can't parse teacher's schedule!",
                content=str(schedule_page),
            )
        return TeacherSchedule.from_tag(grid)

    def _check_for_teachers(self) -> None:
        if not self.for_teachers:
            raise ValueError(
                "This parser instance is not configured for teachers!\n"
                "Please create a new instance with appropriate SenderOptions."
            )

    def get_departments(self) -> list["Department"]:
        """Returns a list of departments"""
        self._check_for_teachers()

        departments_response = self.sender.send_request(method="GET")
        departments_page = self._get_page(departments_response)
        titles = departments_page.find(attrs={"class": "tiles-grid"})
        if not titles:
            raise ParingError("No titles found!", content=str(departments_page))
        departments_tags = titles.find_all(name="a", attrs={"data-role": "tile"})
        departments = []
        for tag in departments_tags:
            departments.append(Department.from_tag(tag))
        return departments

    def get_teachers_by_department(self, department_id: int) -> "list[Teacher]":
        """Returns a list of teachers by department id"""
        self._check_for_teachers()

        teachers_response = self.sender.send_request(
            method="GET",
            params={"page": "department", "dep": department_id},
        )
        teachers_page = self._get_page(teachers_response)
        teachers_tags = teachers_page.find_all(attrs={"class": "tiles-grid"})
        if not teachers_tags:
            raise ParingError("No teachers found!", content=str(teachers_page))
        teachers_tags = teachers_tags[0].find_all(
            name="a",
            attrs={"data-role": "tile"},
        )
        teachers = []
        for tag in teachers_tags:
            teachers.append(Teacher.from_tag(tag))
        return teachers
