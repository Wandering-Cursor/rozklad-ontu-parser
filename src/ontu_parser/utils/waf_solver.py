"""
This is a module with classes capable of parsing and passing 2WAF JavaScript challenge.
"""

import asyncio
import re
import urllib.parse
from base64 import b64encode
from hashlib import sha256
import time

from bs4 import BeautifulSoup
from ontu_parser.dataclasses import Cookies


class JavaScriptParser:
    # pylint: disable=too-few-public-methods
    """
    Parses JavaScript from HTML to get necessary values
    """

    def __init__(self: "JavaScriptParser", html: str) -> None:
        self.html = html
        self.soup = BeautifulSoup(html, "html.parser")

        self._notbot_value: str = ""
        self._pow_result: str = ""

    def _extract_script_tags(self: "JavaScriptParser") -> list[str]:
        return [script.text for script in self.soup.find_all("script")]

    def _get_notbot_cookie(
        self: "JavaScriptParser",
        notbot_script: str,
    ) -> str:
        self._notbot_value = (
            notbot_script.split("setCookie('notbot','")[1].split("');")[0].strip()
        )
        return self._notbot_value

    def __make_combinations(
        self: "JavaScriptParser",
        characters: str,
        length: int,
    ) -> list[str]:
        if length == 0:
            return [""]
        return [
            char + combination
            for char in characters
            for combination in self.__make_combinations(characters, length - 1)
        ]

    def _get_pow_result(
        self: "JavaScriptParser",
        pow_script: str,
    ) -> str:
        pow_script = pow_script.replace("\n", "")
        hash_search = re.search(
            r'const hash4find\s*=\s*["\'](.*?)["\']',
            pow_script,
            re.IGNORECASE,
        )

        if not hash_search:
            raise ValueError("Could not find hash4find in pow_script")

        expected_hash = hash_search.group(1)

        combination_characters_search = re.search(
            r'const chars\s*=\s*["\'](.*?)["\']',
            pow_script,
            re.IGNORECASE,
        )

        if not combination_characters_search:
            raise ValueError("Could not find chars in pow_script")

        combination_characters = combination_characters_search.group(1)

        combination_prefix_search = re.search(
            r'const prefix\s*=\s*["\'](.*?)["\']', pow_script, re.IGNORECASE
        )

        if not combination_prefix_search:
            raise ValueError("Could not find prefix in pow_script")

        combination_prefix = combination_prefix_search.group(1)

        combination_length_search = re.search(
            r"const suffixlen\s*=\s*(\d+)",
            pow_script,
            re.IGNORECASE,
        )

        if not combination_length_search:
            raise ValueError("Could not find suffixlen in pow_script")

        combination_length = int(combination_length_search.group(1))

        for combination in self.__make_combinations(
            combination_characters,
            combination_length,
        ):
            hash_string = combination_prefix + combination

            hash_value = sha256(bytes(hash_string, "utf-8")).hexdigest()

            if hash_value == expected_hash:
                self._pow_result = b64encode(
                    urllib.parse.unquote_plus(urllib.parse.quote(hash_string)).encode()
                ).decode()
                return self._pow_result

        raise ValueError("Could not find pow_result")

    def parse(self: "JavaScriptParser") -> Cookies:
        """
        This methods parses JavaScript from HTML and returns CookieValues object
        """
        start = time.time()
        script_tags = self._extract_script_tags()
        pow_result_script: str | None = None

        for script in script_tags:
            script = script.strip()

            if "document.onreadystatechange" in script:
                self._get_notbot_cookie(script)
                continue
            if '"use strict"' in script or "const hash4find" in script:
                pow_result_script = script
                continue
        if not pow_result_script:
            raise ValueError("Could not find pow_result script")

        self._get_pow_result(pow_result_script)
        end = time.time()

        # Stupid artificial delay posed by the website
        # 5.5 should be fine, but I'll add 0.5 just in case
        duration = end - start
        min_duration = 6
        if duration < min_duration:
            time.sleep(min_duration - duration)

        return Cookies(
            value={
                "notbot": self._notbot_value,
                "pow-result": self._pow_result,
            }
        )

    async def async_parse(self: "JavaScriptParser") -> Cookies:
        start = time.time()
        script_tags = self._extract_script_tags()
        pow_result_script: str | None = None

        for script in script_tags:
            script = script.strip()

            if "document.onreadystatechange" in script:
                self._get_notbot_cookie(script)
                continue
            if '"use strict"' in script or "const hash4find" in script:
                pow_result_script = script
                continue
        if not pow_result_script:
            raise ValueError("Could not find pow_result script")

        self._get_pow_result(pow_result_script)
        end = time.time()

        # Stupid artificial delay posed by the website
        # 5.5 should be fine, but I'll add 0.5 just in case
        duration = end - start
        min_duration = 6
        if duration < min_duration:
            await asyncio.sleep(min_duration - duration)

        return Cookies(
            value={
                "notbot": self._notbot_value,
                "pow-result": self._pow_result,
            }
        )
