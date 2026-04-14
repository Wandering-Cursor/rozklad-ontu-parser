from ontu_parser.dataclasses.pair import StudentsPair, TeachersPair
from ontu_parser.dataclasses.base import BaseTag


from bs4.element import Tag


class BaseSchedule(BaseTag):
    """Describes schedule from BS4 tag"""

    schedule_tag: Tag

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._schedule_data: dict[str, list["StudentsPair | TeachersPair"]] = {}

    @property
    def week(self):
        """Gets data for this week"""
        self._get_week()
        return self._schedule_data

    def _get_week(self):
        raise NotImplementedError("`_get_week` was not implemented")


class StudentsSchedule(BaseSchedule):
    """Describes schedule from HTML table"""

    subgroup_id: int = 0
    _subgroup: str = ""

    _splitter_class: str = "bg-darkCyan"

    def __init__(self, *args, **kwargs):
        self.subgroups: list[str] = []
        super().__init__(*args, **kwargs)

    @staticmethod
    def _check_tag(tag):
        if tag.name != "table":
            raise ValueError(f"Invalid tag: {tag}. Should be table", tag)

    @classmethod
    def from_tag(cls, tag, subgroup=None):
        cls._check_tag(tag)
        obj = cls()
        obj.schedule_tag = tag

        obj._subgroup = subgroup
        obj._get_subgroup_id()

        return obj

    def _get_subgroup_id(self):
        if self._subgroup:
            if not self.subgroups:
                self._parse_subgroups()
            try:
                self.subgroup_id = self.subgroups.index(self._subgroup)
            except ValueError:
                print("Invalid subgroup! Please try making request again")

    def _parse_subgroups(self):
        """This method prepares subgroups for later use"""
        sub_groups_list = []
        table_head = self.schedule_tag.thead
        head_rows = table_head.find_all(name="tr")

        # Hardcoding positions! Yikes!
        # head_rows[0] - meta info (`Day`, `Pair` columns, Group name)
        # head_rows[1] - sub_groups (a/b etc)

        sub_groups_tag = head_rows[1]
        sub_groups_tags = sub_groups_tag.find_all(name="th")

        for sub_group in sub_groups_tags:
            sub_groups_list.append(sub_group.text.strip())

        self.subgroups = sub_groups_list

    def _prepare_day_tag(self, day_name_tag):
        """
        Parses day from 'day_name_tag'*
        Returns name of that day and a list of tags that represent pairs

        *day_name_tag is a tag that contains name of the tag
         It also has attr - class = day
        """
        pair_tags = []

        day_name: str = day_name_tag.text

        first_pair_tag = day_name_tag.parent
        # We also have to include this 'top tag', since it's first pair
        pair_tags.append(first_pair_tag)

        next_pair_tag = first_pair_tag.next_sibling
        # next_sibling gives next tag on the same level of hierarchy
        while True:
            if not next_pair_tag or isinstance(next_pair_tag, str):
                # We may not have next sibling
                # Or, as it happens RN - we may get '  ' as next tag :|
                break
            if self._splitter_class in next_pair_tag.attrs.get("class", []):
                # splitter has class `_splitter_class` (like bg-darkCyan)
                # if we hit splitter - day has ended
                break
            pair_tags.append(next_pair_tag)
            next_pair_tag = next_pair_tag.next_sibling
        if isinstance(pair_tags[-1], str):
            pair_tags.pop()
        return day_name, pair_tags

    def _prepare_tags(self, tags):
        """Parses bs4 tags to list of Pair objects"""
        prepared_tags: list[StudentsPair] = []
        for tag in tags:
            prepared_tags.append(
                StudentsPair.from_tag(tag, subgroup_id=self.subgroup_id)
            )
        return prepared_tags

    def _get_week(self):
        """Iteratively loops trough table to get data for all days"""
        table_body = self.schedule_tag.tbody
        days = table_body.find_all(attrs={"class": "day"})
        for day in days:
            day_name, tags = self._prepare_day_tag(day)
            prepared_days = self._prepare_tags(tags)
            self._schedule_data[day_name] = prepared_days
        return self._schedule_data


class TeacherSchedule(BaseSchedule):
    """Describes schedule from HTML grid"""

    @staticmethod
    def _check_tag(tag: Tag):
        if tag.name != "div":
            raise ValueError(f"Invalid tag: {tag}. Should be div", tag)
        if "grid" not in tag.attrs.get("class", []):
            raise ValueError(f"Invalid tag: {tag}. Should be grid", tag)

    @classmethod
    def from_tag(cls, tag):
        cls._check_tag(tag)
        obj = cls()
        obj.schedule_tag = tag
        return obj

    def _prepare_day_tag(self, day_card: "Tag"):
        day_name = day_card.find(name="div", attrs={"class": "card-header"})
        if not day_name:
            raise ValueError(f"Invalid tag: {day_card}. No card-header found", day_card)
        day_name = day_name.text.strip()
        pairs = []
        for pair in day_card.find_all(name="div", attrs={"data-role": "panel"}):
            pairs.append(pair)
        return day_name, pairs

    def _prepare_tags(self, tags: list["Tag"]):
        prepared_tags: list[TeachersPair] = []
        for tag in tags:
            prepared_tags.append(TeachersPair.from_tag(tag))
        return prepared_tags

    def _get_week(self):
        all_cards = self.schedule_tag.find_all(name="div", attrs={"class": "card"})
        for card in all_cards:
            day_name, tags = self._prepare_day_tag(card)
            prepared_days = self._prepare_tags(tags)
            self._schedule_data[day_name] = prepared_days
        return self._schedule_data
