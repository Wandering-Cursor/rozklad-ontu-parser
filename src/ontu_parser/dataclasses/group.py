from ontu_parser.dataclasses.base import BaseTag


from attrs import define
from bs4.element import Tag


@define
class Group(BaseTag):
    """Describes group from BS4 tag"""

    group_tag: Tag

    _icon_tag_filter = {"attrs": {"class": "icon"}}
    _text_tag_filter = {"attrs": {"class": "branding-bar"}}

    @staticmethod
    def _check_tag(tag):
        attrs = getattr(tag, "attrs", None)
        required = ["data-id"]
        for requirement in required:
            if requirement not in attrs:
                raise ValueError(
                    f"Invalid tag: {tag}, doesn't have attrs: {required}",
                    tag,
                    required,
                )

        # Children requiremenets

        icon = tag.find(**Group._icon_tag_filter)
        text = tag.find(**Group._text_tag_filter)
        required = [icon, text]
        if not all(required):
            raise ValueError(f"Invalid tag: {tag} doesn't have suitable children", tag)

    @classmethod
    def from_tag(cls, tag):
        cls._check_tag(tag)
        return cls(group_tag=tag)

    @property
    def text(self):
        """Returns text tag from group tag"""
        return self.group_tag.find(**self._text_tag_filter)

    @property
    def icon(self):
        """Returns icon tag from group tag"""
        return self.group_tag.find(**self._icon_tag_filter)

    def get_group_id(self):
        """Returns (temporary) id of this group"""
        return self.group_tag.attrs["data-id"]

    def get_group_name(self):
        """Retunrs a name of the group or None"""
        if not self.text:
            print(f"text tag not found in {self.group_tag}")
            return None
        return self.text.string

    def get_group_icon(self):
        """Returns name of the icon of the group or None"""
        if not self.icon:
            print(f"icon tag not found in {self.group_tag}")
            return None
        # Hardcoding this
        attrs = self.icon.attrs.copy()
        # Feels bad :(
        attrs.pop("icon")
        return attrs[0]
