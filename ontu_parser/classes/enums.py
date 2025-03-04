"""Enumerators"""

from enum import Enum, StrEnum


class RequestsEnum:
    """Contains information for Requests library"""

    class Methods(StrEnum):
        """Contains used HTTP Methods for requests"""

        GET = "GET"
        POST = "POST"

        @classmethod
        def choices(cls):
            """Returns list of available choices

            Returns:
                list[str]: list of available choices
            """
            return [cls.GET.value, cls.POST.value]

    class Codes(Enum):
        """Contains used HTTP response codes"""

        OK = 200
        SERVICE_UNAVAILABLE = 503

    @classmethod
    def code_ok(cls):
        """
        OK code

        Returns:
            int: 200, Codes.OK
        """
        return cls.Codes.OK.value

    @classmethod
    def method_get(cls):
        """Method GET

        Returns:
            str: GET
        """
        return cls.Methods.GET.value

    @classmethod
    def method_post(cls):
        """Method POST

        Returns:
            str: POST
        """
        return cls.Methods.POST.value
