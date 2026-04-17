import logging

from ontu_parser.settings import instance

if instance.log_to_file:
    logging.basicConfig(
        level=instance.log_level.value,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(instance.log_file_path),
            logging.StreamHandler(),
        ],
    )
else:
    logging.basicConfig(
        level=instance.log_level.value,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler()],
    )

main_logger = logging.getLogger(__name__)

request_logger = logging.getLogger(f"{__name__}.request_sender")
request_logger.setLevel(instance.request_log_level.value)
