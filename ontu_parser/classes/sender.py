"""Module for sending operations"""
from datetime import datetime
import requests
from selenium import webdriver
from selenium.webdriver import FirefoxOptions

from .base import BaseClass
from .enums import RequestsEnum

class TTLValue(BaseClass):
    """Describes value with some time to live (like authorization token)"""
    _ttl: int = 1800  # Time To Live (in seconds)
    _value: object = None

    issued_at: datetime = datetime.min

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.issued_at = datetime.now()

    def is_valid(self):
        """
            Checks wether value is still valid
                True if TTLValue was issued less seconds before than Time To Live
        """
        seconds_passed = (datetime.now() - self.issued_at).seconds
        if seconds_passed < self._ttl:
            return True
        return False

    def set_value(self, value):
        """Sets value, and resets issued_at"""
        self.issued_at = datetime.now()
        self._value = value
        return self._value


class Cookies(TTLValue):
    """Describes cookies (Temporary values) for requests"""

    def __init__(self, sender, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sender: Sender = sender

    @property
    def value(self) -> dict[str, str]:
        """Returns value of a cookie (or gets one, if not present)"""
        if self._value and self.is_valid():
            return self._value

        print("Cookies are being updated")
        cookie = self.get_cookie()
        if not cookie:
            raise RuntimeError("Could not get cookies")
        return cookie

    def get_cookie(self):
        """Get's cookie value and notbot (used to verify that request is made by human)"""
        link = self.sender.link
        notbot = self.sender.notbot.value

        response = requests.get(
            link,
            cookies={
                'notbot': notbot
            },
            timeout=30
        )
        key = 'PHPSESSID'
        cookie = response.cookies.get(key)

        return self.set_value({key: cookie, 'notbot': notbot})


class NotBot(TTLValue):
    """Describes NotBot value for requests"""

    _browser_kwargs = {}

    @classmethod
    def create(cls, **browser_settings):
        """
            Creates NotBot with certain browser_settings
            Refer to webdriver.Firefox arguments and docs for more info
        """
        if isinstance(browser_settings, dict) and 'browser_settings' in browser_settings:
            # I'm not sure if this is the right way of multi-passing kwargs :|
            browser_settings = browser_settings.get('browser_settings', {})

        obj = cls()
        obj._browser_kwargs = browser_settings

        return obj

    @property
    def value(self) -> str:
        """Returns or sets and returns value of 'notbot'"""
        if self._value and self.is_valid():
            return self._value

        print("Notbot is being updated")
        notbot = self.get_notbot()
        if not notbot:
            raise RuntimeError("Could not get notbot")
        return notbot

    def get_notbot(self):
        """Gets notbot by making webdriver request (emulates JS)"""
        options = self._browser_kwargs.pop('options', None)
        if not options:
            options = FirefoxOptions()
            options.add_argument("--headless")
        driver = webdriver.Firefox(options=options, **self._browser_kwargs)
        driver.get('https://rozklad.ontu.edu.ua/guest_n.php')
        notbot: str | None = None
        while True:
            if notbot:
                break
            cookies = driver.get_cookies()
            if cookies:
                for cookie in cookies:
                    if cookie['name'] == 'notbot':
                        notbot = cookie['value']
        driver.close()
        return self.set_value(notbot)


class Sender(BaseClass):
    """Describes sender with link, notbot and cookies to send requests"""
    link: str = 'https://rozklad.ontu.edu.ua/guest_n.php'
    notbot: NotBot = None
    cookies: Cookies = None

    def __init__(self, *args, **kwargs):
        notbot_kwargs = kwargs.get('notbot', {})
        self.notbot = NotBot.create(**notbot_kwargs)
        self.cookies = Cookies(self)

    _responses: list[requests.Response] = []

    def send_request(self, method: str, data: (dict | None) = None):
        """Sends request with method and some data, if needed"""
        session = requests.Session()
        if method not in RequestsEnum.Methods.CHOICES.value:
            raise ValueError(
                f'arg. `method` should be one of: {RequestsEnum.Methods.CHOICES.value}',
                method,
            )

        try:
            response: requests.Response = session.request(
                method=method,
                url=self.link,
                cookies=self.cookies.value,
                data=data
            )
        except Exception as exception:
            raise ValueError(
                f'could not get response from {self.link}, got exception: {exception}',
                self.link,
                exception
            ) from exception
        if response.status_code != RequestsEnum.code_ok():
            raise ValueError(
                'server returned non OK response',
                response.status_code,
                response,
                response.content
            )
        # Keep resonses for a little while
        self._responses.append(response)
        self._responses = self._responses[-5:]

        return response
