from functools import cached_property

from bs4.element import Tag

from ontu_parser.dataclasses.base import BaseTag
from ontu_parser.dataclasses.lesson import (
    BaseStudentsLesson,
    StudentsRegularLesson,
    TeachersLesson,
)


class StudentsPair(BaseTag):
    """
    Describes pair from bs4 tag

    Note: Pair describes when certain Lesson will happen
    """

    pair_tag: Tag

    pair_no: int | None = None
    _subgroup_id: int = 0

    def __init__(self, *args, **kwargs) -> None:  # noqa: ANN002, ANN003
        self.lessons: list[BaseStudentsLesson] = []
        super().__init__(*args, **kwargs)

    @staticmethod
    def _check_tag(tag: Tag) -> None:
        pass

    @classmethod
    def from_tag(cls, tag: Tag, subgroup_id: int = 0) -> "StudentsPair":
        cls._check_tag(tag)
        obj = cls()
        obj._subgroup_id = subgroup_id

        obj.pair_tag = tag
        obj.set_pair_number()
        pair = obj.pair_tag_for_subgroup
        lessons = cls.get_lessons(pair)
        obj.lessons = lessons
        return obj

    def set_pair_number(self) -> None:
        """This method gets pair number for better identification"""
        pair_no_tag = self.pair_tag.find(attrs={"class": "lesson"})

        assert pair_no_tag is not None, "Could not find pair number tag"

        self.pair_no = int(pair_no_tag.text)

    @cached_property
    def pair_tag_for_subgroup(self) -> Tag:
        """
        This method returns tag for this pair accounting for subgroup
        Currently opening a page for subgroup (like KN-321[a]) opens
        a page for both subgroups (or a group), thus we have to get a correct cell
        """
        pair_no_tag = self.pair_tag.find(attrs={"class": "lesson"})

        assert pair_no_tag is not None, "Could not find pair number tag"

        skip = 1 + self._subgroup_id

        pair_tag: Tag | None = None
        for _ in range(skip):
            pair_tag = pair_no_tag.nextSibling if not pair_tag else pair_tag.nextSibling

        assert pair_tag is not None, "Could not find pair tag for subgroup"

        return pair_tag

    @staticmethod
    def get_lessons(pair: Tag) -> list[StudentsRegularLesson]:
        """Parses lessons for this pair"""
        # All time 'days' have <span>s with dates in them
        all_dates = pair.find_all(name="span", attrs={"class": "fg-blue"})
        # There is at least one tag with this class if
        # there are lessons
        lesson = pair.find(attrs={"class": "predm"})
        lessons = []
        if not any([len(all_dates), lesson]):
            return lessons
        if len(all_dates) > 0:
            # This means we are dealing with 'all time' records
            # Which have multiple lessons per pair
            for lesson in all_dates:
                lessons.append(StudentsRegularLesson.from_tag(lesson))
            return lessons
        # This means we are dealing with single week records
        lessons.append(StudentsRegularLesson.from_tag(lesson))
        return lessons


class TeachersPair(BaseTag):
    """Describes pair from bs4 tag"""

    __pair_no_not_specified = "Не вказано"  # noqa: RUF001
    __pair_name_not_specified = "Назва не вказана"
    __groups_not_specified = "Групи не вказані"

    pair_tag: Tag
    pair_no: int
    lesson: TeachersLesson | None

    @staticmethod
    def _check_tag(tag: Tag) -> None:
        pass

    def parse_tag(self) -> None:
        """This method parses bs4 and stores data from it in object's fields"""
        pair_no_text = self.pair_tag.attrs.get("data-title-caption", self.__pair_no_not_specified)
        if pair_no_text != self.__pair_no_not_specified:
            self.pair_no = int(pair_no_text.split()[0])
        else:
            self.pair_no = 0

        pair_name_tag = self.pair_tag.find(name="p", attrs={"class": "text-leader"})
        pair_name = pair_name_tag.get_text(strip=True) if pair_name_tag else None

        groups_tag = self.pair_tag.find(name="p", attrs={"class": "text-secondary"})
        groups = groups_tag.get_text(strip=True) if groups_tag else None

        lesson = None
        if pair_name or groups:
            lesson = TeachersLesson(
                name=pair_name or self.__pair_name_not_specified,
                groups=groups or self.__groups_not_specified,
            )

        self.lesson = lesson

    @classmethod
    def from_tag(cls, tag: Tag) -> "TeachersPair":
        cls._check_tag(tag)
        obj = cls()
        obj.pair_tag = tag
        obj.parse_tag()
        return obj
