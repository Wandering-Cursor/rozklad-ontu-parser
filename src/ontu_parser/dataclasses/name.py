from ontu_parser.dataclasses.base import BaseSchema


class NameRepresentation(BaseSchema):
    """Describes teacher's name"""

    short: str
    full: str
