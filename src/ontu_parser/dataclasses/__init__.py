"""
Contains classes needed to get data
Like Faculty or Group, provides methods to get names, ids, etc.
"""

from .department import Department
from .faculty import Faculty
from .group import Group
from .lesson import BaseStudentsLesson, StudentsRegularLesson, TeachersLesson
from .pair import StudentsPair, TeachersPair
from .schedule import StudentsSchedule, TeacherSchedule
from .teacher import Teacher
from .value_with_ttl import ValueWithTTL, Cookies

__all__ = [
    "Department",
    "Faculty",
    "Group",
    "BaseStudentsLesson",
    "StudentsRegularLesson",
    "TeachersLesson",
    "StudentsPair",
    "TeachersPair",
    "StudentsSchedule",
    "TeacherSchedule",
    "Teacher",
    "ValueWithTTL",
    "Cookies",
]
