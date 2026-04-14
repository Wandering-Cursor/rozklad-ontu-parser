from ontu_parser.dataclasses.base import BaseTag
from ontu_parser.dataclasses.lesson import (
    BaseStudentsLesson,
    StudentsRegularLesson,
    TeachersLesson,
)

from bs4.element import Tag


class StudentsPair(BaseTag):
    """
    Describes pair from bs4 tag

    Note: Pair describes when certain Lesson will happen
    """

    pair_tag: Tag

    pair_no: int | None = None
    _subgroup_id: int = 0

    def __init__(self, *args, **kwargs):
        self.lessons: list[BaseStudentsLesson] = []
        super().__init__(*args, **kwargs)

    @staticmethod
    def _check_tag(tag: Tag):
        pass

    @classmethod
    def from_tag(cls, tag, subgroup_id=0):
        cls._check_tag(tag)
        obj = cls()
        obj._subgroup_id = subgroup_id

        obj.pair_tag = tag
        obj.set_pair_number()
        pair = obj.get_pair_tag_for_subgroup()
        lessons = cls.get_lessons(pair)
        obj.lessons = lessons
        return obj

    def set_pair_number(self):
        """This method gets pair number for better identification"""
        pair_no_tag = self.pair_tag.find(attrs={"class": "lesson"})
        self.pair_no = int(pair_no_tag.text)

    def get_pair_tag_for_subgroup(self):
        """
        This method returns tag for this pair accounting for subgroup
        Currently opening a page for subgroup (like KN-321[a]) opens
        a page for both subgroups (or a group), thus we have to get a correct cell
        """
        pair_no_tag = self.pair_tag.find(attrs={"class": "lesson"})
        skip = 1 + self._subgroup_id
        pair_tag = None
        for _ in range(skip):
            if not pair_tag:
                pair_tag = pair_no_tag.nextSibling
            else:
                pair_tag = pair_tag.nextSibling
        return pair_tag

    @staticmethod
    def get_lessons(pair: Tag):
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

    __pair_no_not_specified = "Не вказано"
    __pair_name_not_specified = "Назва не вказана"
    __groups_not_specified = "Групи не вказані"

    pair_tag: Tag
    pair_no: int
    lesson: TeachersLesson | None

    @staticmethod
    def _check_tag(tag: Tag):
        pass

    def parse_tag(self):
        """This method parses bs4 and stores data from it in object's fields"""
        pair_no_text = self.pair_tag.attrs.get(
            "data-title-caption", self.__pair_no_not_specified
        )
        if pair_no_text != self.__pair_no_not_specified:
            self.pair_no = int(pair_no_text.split()[0])
        else:
            self.pair_no = 0

        pair_name_tag = self.pair_tag.find(name="p", attrs={"class": "text-leader"})
        pair_name = pair_name_tag.text.strip() if pair_name_tag else None

        groups_tag = self.pair_tag.find(name="p", attrs={"class": "text-secondary"})
        # Consider splitting. e.g of content: КН-341[а], КН-342[а], КН-343[а], КН-343[б]
        groups = groups_tag.text.strip() if groups_tag else None

        lesson = None
        if pair_name or groups:
            lesson = TeachersLesson(
                name=pair_name or self.__pair_name_not_specified,
                groups=groups or self.__groups_not_specified,
            )

        self.lesson = lesson

    @classmethod
    def from_tag(cls, tag):
        cls._check_tag(tag)
        obj = cls()
        obj.pair_tag = tag
        obj.parse_tag()
        return obj
