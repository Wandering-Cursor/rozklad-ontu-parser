"""
If you try running this script multiple times, you'll notice that
for each cookie you get different Group IDs. That's because their IDs are tied to the PHP Session.

Thus, you CANNOT use Group IDs to store groups in database, and should fetch groups by name each time.
"""

from ontu_parser.parser import Parser
from ontu_parser.utils.logging import main_logger


def main() -> None:
    parser = Parser()

    faculties = parser.get_faculties()

    for faculty in faculties:
        main_logger.info(f"Faculty: {faculty.faculty_name} ({faculty.faculty_id})")

    faculty_name = input("Enter faculty name to get groups of: ")

    faculty = next(filter(lambda f: f.faculty_name == faculty_name, faculties), None)

    if faculty is None:
        main_logger.warning(f"{faculty_name} faculty not found")
        return

    groups = parser.get_groups(faculty=faculty)

    for group in groups:
        main_logger.info(f"Group: {group.group_name} ({group.group_id})")


if __name__ == "__main__":
    main()
