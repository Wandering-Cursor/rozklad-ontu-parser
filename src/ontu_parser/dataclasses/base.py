"""Module with base classes"""

import keyword
from typing import Any

from attrs import define
from bs4.element import Tag
from pydantic import BaseModel, ConfigDict

reserved_names = keyword.kwlist


@define
class BaseClass:
    """Provides common base for descendants"""

    def __init__(self, *args, **kwargs) -> None:  # noqa: ANN002, ANN003
        """Mock to allow using __init__ with args and kwargs (see Parser class)"""

    def get_as_str(self) -> str:
        """Returns __dict__ in a string format"""
        return str(self.__dict__)

    def get_class_as_str(self) -> str:
        """Returns __class__ in a string formt"""
        return str(self.__class__)

    def __repr__(self) -> str:
        return str(self.to_dict())

    # pylint: disable=C0301
    # Copied from https://github.com/MarshalX/yandex-music-api/blob/a30082f4929e56381c870cb03103777ae29bcc6b/yandex_music/base.py
    # Thanks to MarshalX for this amazing serializer
    # *Added pylint disable!
    def to_dict(self, for_request=False) -> dict | list | Any:  # noqa: ANN001, ANN401
        # pylint: disable=R1705, C0103, C0301
        """Рекурсивная сериализация объекта.
        Args:
            for_request (:obj:`bool`): Перевести ли обратно все поля в camelCase и игнорировать зарезервированные слова.
        Note:
            Исключает из сериализации `client` и `_id_attrs` необходимые в `__eq__`.
            К зарезервированным словам добавляет "_" в конец.
        Returns:
            :obj:`dict`: Сериализованный в dict объект.
        """  # noqa: E501, RUF002

        def parse(val: BaseClass | Any) -> dict | list | Any:  # noqa: ANN401
            # Added by Me - bs4 objects have any attr
            if hasattr(val, "to_dict") and val.to_dict:
                return val.to_dict(for_request)
            if isinstance(val, list):
                return [parse(it) for it in val]
            if isinstance(val, dict):
                return {key: parse(value) for key, value in val.items()}
            if isinstance(val, Tag):
                return {val.__class__: val.name}
            return val

        data = self.__dict__.copy()
        # Removed nonexistent pops
        # data.pop('client', None)
        # data.pop('_id_attrs', None)

        if for_request:
            for k, v in data.copy().items():
                camel_case = "".join(word.title() for word in k.split("_"))
                camel_case = camel_case[0].lower() + camel_case[1:]

                data.pop(k)
                data.update({camel_case: v})
        else:
            for k, v in data.copy().items():
                if k.lower() in reserved_names:
                    data.pop(k)
                    data.update({f"{k}_": v})

        return parse(data)


class BaseTag(BaseClass):
    """Base Tag Class for parsing BS4 tags from responses"""

    @classmethod
    def from_tag(cls, tag: Tag) -> "BaseTag":
        """Checks tag and returns initialized object"""
        raise NotImplementedError("`from_tag` Not implemented")

    @staticmethod
    def _check_tag(tag: Tag) -> None:
        """Checks if tag is valid for usage"""
        raise NotImplementedError("`_check_tag` Not implemented")


class BaseSchema(BaseModel):
    """A modern base class for schemas, based on Pydantic's BaseModel"""

    model_config = ConfigDict(
        from_attributes=True,
    )
