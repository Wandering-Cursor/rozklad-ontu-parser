from functools import cached_property

from ontu_parser.dataclasses.base import BaseTag


from attrs import define
from bs4.element import Tag


@define
class Faculty(BaseTag):
    """Describes faculty from BS4 tag"""

    parent_id: int | None
    prefix: str
    faculty_tag: Tag

    @staticmethod
    def _check_tag(tag):
        attrs = getattr(tag, "attrs", None)
        span = getattr(tag, "span", None)
        required_properties = [attrs, span]
        if not all(required_properties):
            raise ValueError(f"Invalid tag: {tag}, has no attrs", tag)
        required = ["data-id"]
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
    def from_tag(
        cls,
        tag,
        prefix: str = "",
        parent_id: int | None = None,
    ):
        cls._check_tag(tag)
        return cls(
            faculty_tag=tag,
            prefix=prefix,
            parent_id=parent_id,
        )

    @cached_property
    def faculty_picture(self) -> str | None:
        """Returns relative link to picture (if present)"""
        data_cover = self.faculty_tag.attrs.get("data-cover", None)

        if isinstance(data_cover, list):
            return data_cover[0]

        return data_cover

    @cached_property
    def faculty_id(self) -> int:
        """Returns temporary id of faculty (for later use in search)"""
        result = self.faculty_tag.attrs["data-id"]
        if isinstance(result, list):
            return int(result[0])
        return int(result)

    @cached_property
    def faculty_name(self) -> str:
        """Returns name of the faculty"""
        name = (self.faculty_tag.span.string if self.faculty_tag.span else None) or ""

        if self.prefix:
            return f"{self.prefix} {name}".strip()

        return name.strip()
