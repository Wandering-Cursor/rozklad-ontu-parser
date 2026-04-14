from bs4 import BeautifulSoup
from httpx import Response

from ontu_parser.dataclasses.base import BaseClass
from ontu_parser.dataclasses import (
    StudentsSchedule,
    TeacherSchedule,
    Teacher,
    Department,
    Group,
    Faculty,
)
from ontu_parser.dataclasses.sender import SenderOptions
from ontu_parser.errors import ParingError
from ontu_parser.utils.request_sender import RequestSender


class Parser(BaseClass):
    """Parser class to get information from Rozklad ONTU"""

    def __init__(
        self,
        sender_options: SenderOptions | None = None,
    ):
        if sender_options:
            self.sender = RequestSender(
                api_url=sender_options.api_url,
                for_teachers=sender_options.for_teachers,
                cookies=sender_options.cookies,
                cookies_issued_at=sender_options.cookies_issued_at,
            )
        else:
            self.sender = RequestSender()

    def _get_page(self, response: Response) -> BeautifulSoup:
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
        faculties_response = self.sender.send_request(
            method="GET"  # No data gives 'main' page with faculties
        )
        faculty_page = self._get_page(faculties_response)
        faculty_tags = faculty_page.find_all(
            attrs={"class": "fc"}
        )  # Faculties have class 'fc'
        faculty_entities = []
        for tag in faculty_tags:
            faculty_entities.append(Faculty.from_tag(tag))
        return faculty_entities

    def get_all_extramurals(self) -> list[Faculty]:
        """Returns a list of extramural faculties"""
        faculties = self.get_faculties()
        extramurals = []
        for faculty in faculties:
            extramural = self.get_extramural(int(faculty.get_faculty_id()))
            if extramural:
                extramurals.append(extramural)

        return extramurals

    def get_extramural(self: "Parser", faculty_id: int) -> Faculty | None:
        """
        Returns extramural faculty by faculty id
        Returns None if no extramural faculty found
        """
        # TODO: Here we need to follow some specific sequence to get the
        # extramural faculty.
        # Getting two in a row causes problems
        faculty_data = self.sender.send_request(
            method="POST",
            data={"facultyid": faculty_id},
        )
        faculty_page = self._get_page(faculty_data)
        faculty_tag = faculty_page.find(attrs={"class": "fc"})
        faculty_name_tag = faculty_page.find(attrs={"href": "?to_faculty=1"})
        if faculty_tag:
            return Faculty.from_tag(
                faculty_tag,
                prefix=(faculty_name_tag.text + " - ") if faculty_name_tag else "",
                parent_id=faculty_id,
            )
        return None

    def get_groups(
        self,
        faculty_id: int | str | None = None,
        faculty: Faculty | None = None,
    ) -> list[Group]:
        """Returns Group list of a faculty by faculty id"""
        if isinstance(faculty_id, str):
            faculty_id = int(faculty_id)
        if isinstance(faculty, Faculty):
            faculty_id = int(faculty.get_faculty_id())
            if faculty.parent_id:
                # Someone has decided that extramural groups can only be seen if you have seen this
                # specific parent first :shrug:
                # Apparently, they've changed it, and now you need to do the opposite:
                # Visit parent, then a specific faculty ID
                # Both are stupid. I'd better notify someone about this, but like they'll care...
                self.get_groups(faculty_id=faculty.parent_id)

        if not any([faculty_id, faculty]):
            raise ValueError("Please specify one of the optional parameters")

        groups_response = self.sender.send_request(
            method="POST",
            data={"facultyid": faculty_id},
        )
        groups_page = self._get_page(groups_response)
        groups_tags = groups_page.find_all(attrs={"class": "grp"})
        group_entities: list[Group] = []
        for tag in groups_tags:
            group_entities.append(Group.from_tag(tag))
        return group_entities

    def get_schedule(
        self,
        group_id: int | None = None,
        teacher_id: int | None = None,
        all_time=False,
    ):
        """Returns schedule for group, or for teachers"""
        if group_id:
            return self._get_group_schedule(group_id, all_time=all_time).week
        if teacher_id:
            return self._get_teachers_schedule(teacher_id, all_time=all_time).week
        raise ValueError("No group or teacher id provided!")

    def _get_group_schedule(self, group_id, all_time=False) -> StudentsSchedule:
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
                message="No breadcrumbs found! Can't parse schedule without breadcrumbs!",
                content=str(schedule_page),
            )

        group_breadcrumbs = breadcrumbs.find_all(attrs={"class": "page-link"})

        table = schedule_page.find(attrs={"class": "table"})
        group_name = group_breadcrumbs[-1].text
        # I hate this, but at the same time - I love it
        # If it ever to become broken I'll implement this a bit thoughtfully :)
        subgroup_name = group_name.split("[")[1].replace("]", "")
        schedule = StudentsSchedule.from_tag(table, subgroup=subgroup_name)
        return schedule

    def _get_teachers_schedule(self, teacher_id, all_time=False) -> TeacherSchedule:
        """Returns a schedule for a teacher (by id)"""
        self._check_for_teachers()
        query = {"page": "teacher", "teacher": teacher_id}
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
            raise ParingError("No grid found!", content=str(schedule_page))
        schedule = TeacherSchedule.from_tag(grid)
        return schedule

    def _check_for_teachers(self):
        """A check, that must be rune before executing teachers methods"""
        if not self.sender:
            raise ParingError("Sender is not set!")
        if not self.sender._for_teachers:
            raise ParingError("Sender is not set for teachers!")

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
