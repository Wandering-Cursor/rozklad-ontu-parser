from functools import cached_property
from typing import Any

from attrs import define
from bs4.element import Tag

from ontu_parser.dataclasses.base import BaseTag
from ontu_parser.utils.logging import main_logger


@define
class Group(BaseTag):
    """Describes group from BS4 tag"""

    group_tag: Tag

    @staticmethod
    def _check_tag(tag: Tag) -> None:
        attrs: list = getattr(tag, "attrs", None)  # pyright: ignore[reportAssignmentType]
        required = ["data-id"]
        for requirement in required:
            if requirement not in attrs:
                raise ValueError(
                    f"Invalid tag: {tag}, doesn't have attrs: {required}",
                    tag,
                    required,
                )

        # Children requirements
        icon = tag.find(attrs={"class": "icon"})
        text = tag.find(attrs={"class": "branding-bar"})
        required = [icon, text]
        if not all(required):
            raise ValueError(f"Invalid tag: {tag} doesn't have suitable children", tag)

    @classmethod
    def from_tag(cls, tag: Any) -> "Group":  # noqa: ANN401
        cls._check_tag(tag)

        return cls(group_tag=tag)

    @cached_property
    def text(self):  # noqa: ANN201
        """Returns text tag from group tag"""
        return self.group_tag.find(attrs={"class": "branding-bar"})

    @cached_property
    def icon(self):  # noqa: ANN201
        """Returns icon tag from group tag"""
        return self.group_tag.find(attrs={"class": "icon"})

    @cached_property
    def group_id(self) -> str:
        """Returns id of this group"""
        value = self.group_tag.attrs["data-id"]

        if isinstance(value, list):
            return value[0]

        return value

    @cached_property
    def group_name(self) -> str | None:
        """Retunrs a name of the group or None"""
        if not self.text:
            main_logger.warning(f"Could not find text tag in {self.group_tag}")
            return None

        return self.text.string

    @cached_property
    def group_icon(self) -> str | None:
        """Returns name of the icon of the group or None"""
        if not self.icon:
            main_logger.warning(f"Could not find icon tag in {self.group_tag}")
            return None

        classes = self.icon.attrs.get("class", [])
        if isinstance(classes, str):
            classes = classes.split()

        if "icon" in classes:
            classes.remove("icon")

        if len(classes) == 0:
            return None

        return classes[0]
