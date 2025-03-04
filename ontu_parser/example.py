"""Usage example"""
# To test Library installed from PyPi, use this import:

from ontu_parser.classes import Parser

# To test Library from source code, use this import:

# from classes import Parser

# An example of how to pass arguments to Firefox browser created by selenium
# Add arguments inside 'browser_settings' and see what happens
parser = Parser()

schedule = parser.parse(all_time=False)
for day_name, pairs in schedule.items():
    print(f"{day_name}:\n")
    for pair in pairs:
        if not pair.lessons:
            continue
        print(f"{pair.pair_no}:")
        for lesson in pair.lessons:
            print(
                f"{lesson.lesson_date}: "
                f"{lesson.teacher['short']} - "
                f"{lesson.lesson_name['short']}"
                f" - In auditorium: {lesson.auditorium}"
                if lesson.auditorium
                else ""
            )
            print(f"Card: {lesson.lesson_info}\n")
