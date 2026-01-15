"""Module for parser class"""

from bs4 import BeautifulSoup
from requests import Response

from .base import BaseClass
from .dataclasses import (
    Department,
    Faculty,
    Group,
    StudentsSchedule,
    Teacher,
    TeacherSchedule,
)
from .enums import RequestsEnum
from .sender import Sender


class Parser(BaseClass):
    """Parser class to get information from Rozklad ONTU"""

    sender: Sender

    def __init__(self, *args, **kwargs):
        if isinstance(kwargs, dict) and "kwargs" in kwargs:
            # Trick to unwrap kwargs
            kwargs = kwargs.get("kwargs", {})

        self.sender = Sender(*args, **kwargs)

    def _get_page(self, response: Response):
        content = response.content
        if not content:
            raise ValueError(f"Response: {response} has no content!", response)
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
        main_response = self.sender.send_request(
            method=RequestsEnum.method_get())
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
            method=RequestsEnum.method_get()  # No data gives 'main' page with faculties
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
            extramural = self.get_extramural(faculty.get_faculty_id())
            if extramural:
                extramurals.append(extramural)

        return extramurals

    def get_extramural(self: "Parser", faculty_id: int) -> Faculty | None:
        """
        Returns extramural faculty by faculty id
        Returns None if no extramural faculty found
        """
        faculty_data = self.sender.send_request(
            method=RequestsEnum.method_post(),
            data={"facultyid": faculty_id},
        )
        faculty_page = self._get_page(faculty_data)
        faculty_tag = faculty_page.find(attrs={"class": "fc"})
        faculty_name_tag = faculty_page.find(attrs={"href": "?to_faculty=1"})
        if faculty_tag:
            return Faculty.from_tag(
                faculty_tag,
                prefix=(faculty_name_tag.text +
                        " - ") if faculty_name_tag else "",
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
            method=RequestsEnum.method_post(),
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
            method=RequestsEnum.method_post(),
            data=request_data,
        )
        schedule_page = self._get_page(schedule_response)

        breadcrumbs = schedule_page.find(attrs={"class": "breadcrumbs"})
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
            method=RequestsEnum.method_get(),
            query=query,
        )
        schedule_page = self._get_page(schedule_response)

        grid = schedule_page.find(name="div", attrs={"class": "grid"})
        if not grid:
            raise ValueError("No grid found!")
        schedule = TeacherSchedule.from_tag(grid)
        return schedule

    def parse(self, all_time=False):
        """Parses information, requiring user input (CLI)"""
        schedule = None
        all_faculties = self.get_faculties()

        for faculty in all_faculties:
            print(faculty.get_faculty_name())

        faculty_name = input("Введите название факультета: ")
        faculty_id = None
        for faculty in all_faculties:
            if faculty.get_faculty_name() == faculty_name:
                faculty_id = faculty.get_faculty_id()
                break
        else:
            print("Несуществующее имя факльтета!")
            return schedule
        groups = self.get_groups(faculty_id)
        for group in groups:
            print(group.get_group_name())

        group_name = input("Введите название группы: ")
        group_id = None
        for group in groups:
            if group.get_group_name() == group_name:
                group_id = group.get_group_id()
                break
        else:
            print("Несуществующее имя группы!")
            return schedule

        schedule = self.get_schedule(group_id, all_time=all_time)
        return schedule

    def _check_for_teachers(self):
        """A check, that must be rune before executing teachers methods"""
        if not self.sender:
            raise ValueError("Sender is not set!")
        if not self.sender.for_teachers:
            raise ValueError("Sender is not set for teachers!")

    def get_departments(self) -> list["Department"]:
        """Returns a list of departments"""
        self._check_for_teachers()

        departments_response = self.sender.send_request(
            method=RequestsEnum.method_get()
        )
        departments_page = self._get_page(departments_response)
        titles = departments_page.find(attrs={"class": "tiles-grid"})
        if not titles:
            raise ValueError("No titles found!")
        departments_tags = titles.find_all(
            name="a", attrs={"data-role": "tile"})
        departments = []
        for tag in departments_tags:
            departments.append(Department.from_tag(tag))
        return departments

    def get_teachers_by_department(self, department_id: int) -> "list[Teacher]":
        """Returns a list of teachers by department id"""
        self._check_for_teachers()

        teachers_response = self.sender.send_request(
            method=RequestsEnum.method_get(),
            query={"page": "department", "dep": department_id},
        )
        teachers_page = self._get_page(teachers_response)
        teachers_tags = teachers_page.find_all(attrs={"class": "tiles-grid"})
        if not teachers_tags:
            raise ValueError("No teachers found!")
        teachers_tags = teachers_tags[0].find_all(
            name="a",
            attrs={"data-role": "tile"},
        )
        teachers = []
        for tag in teachers_tags:
            teachers.append(Teacher.from_tag(tag))
        return teachers
