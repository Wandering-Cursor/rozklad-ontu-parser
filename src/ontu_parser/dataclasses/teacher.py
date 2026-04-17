from functools import cached_property
from typing import Any
from urllib.parse import parse_qsl

from attrs import define
from bs4.element import Tag

from ontu_parser.dataclasses.base import BaseTag
from ontu_parser.dataclasses.name import NameRepresentation


@define
class Teacher(BaseTag):
    """Describes teacher from BS4 tag"""

    teacher: Tag

    @staticmethod
    def _check_tag(tag: Any) -> None:  # noqa: ANN401
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
    def from_tag(cls, tag: Any) -> "Teacher":  # noqa: ANN401
        cls._check_tag(tag)
        obj = cls(teacher=tag)
        if not obj.teacher:
            raise ValueError("Invalid tag", tag)
        return obj

    @cached_property
    def teacher_picture(self) -> str | None:
        """Returns class of the picture (if present)"""
        container = self.teacher.find(name="div", attrs={"class": "slide-front"})
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
    def teacher_link(self) -> str:
        """Returns (semi?) permanent relative link to department"""
        value = self.teacher.attrs["href"]
        if isinstance(value, list):
            value = value[0]
        return value

    @cached_property
    def teacher_id(self) -> int:
        """Returns id of the Teacher"""
        key_dict = dict(parse_qsl(self.teacher_link))
        return int(key_dict["teacher"])

    @cached_property
    def teacher_name(self) -> NameRepresentation:
        """Returns name of the Teacher"""

        short_name_span = self.teacher.find(name="span", attrs={"class": "branding-bar"})
        full_name_span = self.teacher.find(name="div", attrs={"class": "slide-back"})

        short_name = short_name_span.get_text(strip=True) if short_name_span else ""
        full_name = full_name_span.get_text(strip=True) if full_name_span else ""

        return NameRepresentation(short=short_name, full=full_name)
