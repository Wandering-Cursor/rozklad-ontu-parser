from functools import cached_property
from urllib.parse import parse_qsl

from attrs import define
from bs4.element import Tag

from ontu_parser.dataclasses.base import BaseTag
from ontu_parser.dataclasses.name import NameRepresentation


@define
class Department(BaseTag):
    """Describes department from BS4 tag"""

    department: Tag

    @staticmethod
    def _check_tag(tag: Tag) -> None:
        attrs: list = getattr(tag, "attrs", None)  # pyright: ignore[reportAssignmentType]
        span = tag.find(name="span", attrs={"class": "branding-bar"})
        required_properties = [attrs, span]
        if not all(required_properties):
            raise ValueError(f"Invalid tag: {tag}, has no attrs", tag)
        required = ["href"]
        for requirement in required:
            if requirement not in attrs:
                raise ValueError(
                    f"Invalid tag: {tag}, doesn't have attrs: {required}",
                    tag,
                    required,
                )
        span_string = getattr(span, "string", None)
        if span_string is None:
            raise ValueError(f"Invalid tag: {tag}, `span` has no string", tag)

    @classmethod
    def from_tag(cls, tag: Tag) -> "Department":
        cls._check_tag(tag)
        obj = cls(department=tag)
        if not obj.department:
            raise ValueError("Invalid tag", tag)
        return obj

    @cached_property
    def department_picture(self) -> str | None:
        """Returns class of the picture (if present)"""
        container = self.department.find(name="div", attrs={"class": "slide-front"})
        if not container:
            return None
        span = container.find(name="span")
        if not span:
            return None

        classes = span.attrs.get("class", [])

        if isinstance(classes, str):
            classes = classes.split()

        if "icon" in classes:
            classes.remove("icon")

        if len(classes) == 0:
            return None

        return classes[0]

    @cached_property
    def department_link(self) -> str:
        """Returns (semi?) permanent relative link to department"""
        value = self.department.attrs["href"]
        if isinstance(value, list):
            return value[0]
        return value

    @cached_property
    def department_id(self) -> int:
        """Return id of the department"""
        key_dict = dict(parse_qsl(self.department_link))

        return int(key_dict["dep"])

    @cached_property
    def department_name(self) -> NameRepresentation:
        """Returns name of the faculty"""
        requires_capitalization_word_length = 2

        short_name_span = self.department.find(name="span", attrs={"class": "branding-bar"})
        full_name_span = self.department.find(name="div", attrs={"class": "slide-back"})
        short_name = short_name_span.get_text(strip=True) if short_name_span else ""
        full_name = full_name_span.get_text(strip=True) if full_name_span else ""

        if full_name:
            words = full_name.split()
            full_name = " ".join(
                [
                    x.capitalize() if len(x) > requires_capitalization_word_length else x
                    for x in words
                ]
            )

        return NameRepresentation(short=short_name, full=full_name)
