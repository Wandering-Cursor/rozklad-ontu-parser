# Rozklad ONTU Pareser

## Badges
[![Pylint](https://github.com/Wandering-Cursor/rozklad-ontu-parser/actions/workflows/pylint.yml/badge.svg?branch=master)](https://github.com/Wandering-Cursor/rozklad-ontu-parser/actions/workflows/pylint.yml)
[![Upload Python Package](https://github.com/Wandering-Cursor/rozklad-ontu-parser/actions/workflows/python-publish.yml/badge.svg)](https://github.com/Wandering-Cursor/rozklad-ontu-parser/actions/workflows/python-publish.yml)

## Links
Available on [PyPi](https://pypi.org/project/rozklad-ontu-parser-MakisuKurisu/)

## Description (ENG)

This library is designed to get the schedule from the [ONTU schedule site](https://rozklad.ontu.edu.ua).

You can find a small example in the [example.py](/ontu_parser/example.py) file.

You can also find our other project that uses this library [here](https://github.com/Wandering-Cursor/ontu-schedule-bot).

## Опис (UKR)

Ця бібліотека призначена для отримання розкладу з [сайту з розкладом ОНТУ](https://rozklad.ontu.edu.ua)

На поточний момент бібліотека може повернути розклад на поточний тиждень, чи на весь семестр. В подальшому планується додати підтримку розкладу екзаменів, повідомлень та інших розділів сайту.

### А як користуватися?
Ви можете подивитися приклад використання в файлі [example.py](/ontu_parser/example.py). Також наразі є окремий метод для отримання розкладу з CLI - parse.
Приклад використання також доступний у нашому боті, який використовує цю бібліотеку, [код - тут](https://github.com/Wandering-Cursor/ontu-schedule-bot).

## Requirements
- [Python](https://python.org) 3.11 or higher
- [PDM Package Manager](https://pdm-project.org/)

## Honorable Mentions
- [MarshalX](https://github.com/MarshalX) за [дозвіл](https://t.me/yandex_music_api/29677) позичити метод `to_dict` з його ліби: [yandex-music-api](https://github.com/MarshalX/yandex-music-api). (Було внесено мінімальні зміни через bs4 теги)
