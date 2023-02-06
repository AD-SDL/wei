from pathlib import Path
from typing import Optional

from rpl_wei.data_classes import PathLike

import logging


class WEI_Logger:
    @staticmethod
    def _create_logger(
        self,
        logger_name: str,
        log_file: Optional[PathLike] = None,
        level: int = logging.INFO,
    ):
        if log_file is None:
            log_file = Path().resolve() / f"{logger_name}.log"
        logger = logging.getLogger(logger_name)
        formatter = logging.Formatter("%(asctime)s (%(levelname)s): %(message)s")
        fileHandler = logging.FileHandler(log_file, mode="a+")
        fileHandler.setFormatter(formatter)
        streamHandler = logging.StreamHandler()
        streamHandler.setFormatter(formatter)

        logger.setLevel(level)
        logger.addHandler(fileHandler)
        logger.addHandler(streamHandler)

        return logger

    @staticmethod
    def get_logger(
        log_name: str,
        log_dir: Optional[Path] = None,
        log_level: int = logging.INFO,
    ) -> logging.Logger:

        logger = (
            WEI_Logger._create_logger(
                log_name,
                log_dir.log_dir / f"{log_name}.log",
                log_level,
            )
            if not logging.getLogger().hasHandlers()
            else logging.getLogger(log_name)
        )
        return logger
