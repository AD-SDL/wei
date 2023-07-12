import logging
from pathlib import Path
from typing import Optional

from rpl_wei.core.data_classes import PathLike


class WEI_Logger:
    """Placeholder"""

    @staticmethod
    def _create_logger(
        logger_name: str,
        log_file: Optional[PathLike] = None,
        level: int = logging.INFO,
    ):
        """Placeholder"""
        if log_file is None:
            log_file = Path().resolve() / f"{logger_name}.log"

        log_file.parent.mkdir(parents=True, exist_ok=True)

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
        """Placeholder"""
        if not logging.getLogger(log_name).hasHandlers():
            logger = WEI_Logger._create_logger(
                log_name,
                log_dir / f"{log_name}.log",
                log_level,
            )
        else:
            logger = logging.getLogger(log_name)
            # for handler in logger.handlers:
            #     logger.removeHandler(handler)
            # log_file = log_dir / f"{log_name}.log"
            # log_file.parent.mkdir(parents=True, exist_ok=True)
            # formatter = logging.Formatter("%(asctime)s (%(levelname)s): %(message)s")
            # fileHandler = logging.FileHandler(log_file, mode="a+")
            # fileHandler.setFormatter(formatter)
            # streamHandler = logging.StreamHandler()
            # streamHandler.setFormatter(formatter)

            # logger.setLevel(log_level)
            # logger.addHandler(fileHandler)
            # logger.addHandler(streamHandler)

        return logger

    @staticmethod
    def to_json(
        log_name: str,
        log_dir: Optional[Path] = None,
        log_level: int = logging.INFO,
    ) -> logging.Logger:
        """Placeholder"""

        if not logging.getLogger(log_name).hasHandlers():
            logger = WEI_Logger._create_logger(
                log_name,
                log_dir / f"{log_name}.log",
                log_level,
            )
        else:
            logger = logging.getLogger(log_name)
            # for handler in logger.handlers:
            #     logger.removeHandler(handler)
            # log_file = log_dir / f"{log_name}.log"
            # log_file.parent.mkdir(parents=True, exist_ok=True)
            # formatter = logging.Formatter("%(asctime)s (%(levelname)s): %(message)s")
            # fileHandler = logging.FileHandler(log_file, mode="a+")
            # fileHandler.setFormatter(formatter)
            # streamHandler = logging.StreamHandler()
            # streamHandler.setFormatter(formatter)

            # logger.setLevel(log_level)
            # logger.addHandler(fileHandler)
            # logger.addHandler(streamHandler)

        return logger
