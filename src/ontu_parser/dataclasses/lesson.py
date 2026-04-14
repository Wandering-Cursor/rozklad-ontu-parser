from ontu_parser.dataclasses.base import BaseTag


from bs4.element import Tag


class BaseStudentsLesson(BaseTag):
    """
    Describes lesson from bs4 tag

    Note: Lesson is a concrete even with date and teacher
    Pair on the other hand just states at which time lesson will happen
    """

    lesson_tag: Tag

    lesson_date: str = ""
    lesson_info: str = ""
    auditorium: str | None = None

    def __init__(self, *args, **kwargs):
        self.teacher: dict = {}
        self.lesson_name: dict = {}
        super().__init__(*args, **kwargs)

    @staticmethod
    def _check_tag(tag: Tag):
        # Dear Gods, forgive me for not checking tags for lessons
        pass

    def parse_tag(self):
        """This method parses bs4 and stores data from it in object's fields"""
        raise NotImplementedError(
            "`parse_tag` was not implemented\n"
            "You are probably executing this from BaseLesson\n"
            "Please use one of derived classes"
        )


class StudentsRegularLesson(BaseStudentsLesson):
    """
    This class should be used to parse lesson from bs4 tag
    If you are getting schedule for current week
    """

    @classmethod
    def from_tag(cls, tag):
        obj = cls()
        obj.lesson_tag = tag
        obj.parse_tag()
        return obj

    def parse_tag(self):
        lesson_top = self.lesson_tag.parent

        predm_element = lesson_top.find(name="span", attrs={"class": "predm"})
        self.lesson_name = {
            "short": predm_element.text,
            "full": predm_element.attrs.get("title", "Not Set"),
        }

        prp_element = lesson_top.find(name="span", attrs={"class": "prp"})
        self.teacher = {
            "short": prp_element.text.replace("\xa0", " "),  # Why...
            "full": prp_element.attrs.get("title", "Not Set"),
        }

        # Card tag consists of two children
        # First states type of content
        # Other - content itself
        card_tag = lesson_top.find(name="div", attrs={"class": "card"})
        if card_tag:
            card_content = card_tag.find(name="div", attrs={"class": "card-content"})
            if card_content:
                self.lesson_info = card_content.text.replace("\t", "").strip()

        auditorium_tag = lesson_top.find(name="a", attrs={"class": "fg-blue"})
        if auditorium_tag:
            self.auditorium = auditorium_tag.text


class TeachersLesson:
    """Class to describe lesson for teachers"""

    # pylint: disable=too-few-public-methods

    name: str
    groups: str

    def __init__(self, name: str, groups: list[str] | str) -> None:
        self.name = name
        if isinstance(groups, list):
            self.groups = ", ".join(groups)
        else:
            self.groups = groups

    def __str__(self) -> str:
        return f"Lesson: {self.name} with ({self.groups})"
