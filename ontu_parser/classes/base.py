"""Module with base classes"""

import keyword

from attrs import define
from bs4.element import Tag

reserved_names = keyword.kwlist


@define
class BaseClass:
    """Provides common base for descendants"""

    def __init__(self, *args, **kwargs):
        """Mock to allow using __init__ with args and kwargs (see Parser class)"""

    def get_as_str(self):
        """Returns __dict__ in a string format"""
        return str(self.__dict__)

    def get_class_as_str(self):
        """Returns __class__ in a string formt"""
        return str(self.__class__)

    def __repr__(self) -> str:
        return str(self.to_dict())

    # pylint: disable=C0301
    # Copied from https://github.com/MarshalX/yandex-music-api/blob/a30082f4929e56381c870cb03103777ae29bcc6b/yandex_music/base.py
    # Thanks to MarshalX for this amazing serializer
    # *Added pylint disable!
    def to_dict(self, for_request=False) -> dict:
        # pylint: disable=R1705, C0103, C0301
        """Рекурсивная сериализация объекта.
        Args:
            for_request (:obj:`bool`): Перевести ли обратно все поля в camelCase и игнорировать зарезервированные слова.
        Note:
            Исключает из сериализации `client` и `_id_attrs` необходимые в `__eq__`.
            К зарезервированным словам добавляет "_" в конец.
        Returns:
            :obj:`dict`: Сериализованный в dict объект.
        """

        def parse(val):
            # Added by Me - bs4 objects have any attr
            if hasattr(val, "to_dict") and val.to_dict:
                return val.to_dict(for_request)
            elif isinstance(val, list):
                return [parse(it) for it in val]
            elif isinstance(val, dict):
                return {key: parse(value) for key, value in val.items()}
            elif isinstance(val, Tag):
                return {val.__class__: val.name}
            else:
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
