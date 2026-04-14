from ontu_parser.dataclasses.base import BaseTag


from attrs import define
from bs4.element import Tag


from urllib.parse import parse_qsl


@define
class Teacher(BaseTag):
    """Describes teacher from BS4 tag"""

    teacher: Tag

    @staticmethod
    def _check_tag(tag):
        attrs = getattr(tag, "attrs", None)
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
    def from_tag(cls, tag):
        cls._check_tag(tag)
        obj = cls(teacher=tag)
        if not obj.teacher:
            raise ValueError("Invalid tag", tag)
        return obj

    def get_teacher_picture(self):
        """Returns class of the picture (if present)"""
        container = self.teacher.find(name="div", attrs={"class": "slide-front"})
        if not container:
            return None
        span = container.find(name="span")
        if not span:
            return None
        return span.attrs.get("class", None)

    def get_teacher_link(self):
        """Returns (semi?) permanent relative link to department"""
        return self.teacher.attrs["href"]

    def get_teacher_id(self) -> int:
        """Return id of teacher"""
        key_dict = dict(parse_qsl(self.get_teacher_link()))
        return int(key_dict["teacher"])

    def get_teacher_name(self) -> dict[str, str]:
        """Returns name of the faculty"""
        name = {"short": "", "full": ""}
        short_name_span = self.teacher.find(
            name="span", attrs={"class": "branding-bar"}
        )
        full_name_span = self.teacher.find(name="div", attrs={"class": "slide-back"})
        name["short"] = short_name_span.text.strip() if short_name_span else ""
        full_name = full_name_span.text.strip() if full_name_span else ""
        name["full"] = full_name
        if full_name:
            words = full_name.split()
            name["full"] = " ".join(
                [x.capitalize() if len(x) > 2 else x for x in words]
            )
        return name
