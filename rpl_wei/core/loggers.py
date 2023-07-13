"""The logging system that helps track events for the system"""
import logging
from pathlib import Path
from typing import Optional

from rpl_wei.core.data_classes import PathLike


class WEI_Logger:
    """The logging system that helps track events for the system"""
    @staticmethod
    def _create_logger(
        logger_name: str,
        log_file: Optional[PathLike] = None,
        level: int = logging.INFO,
    ):
        """Creates a logger that attaches to the given file

         Parameters
         ----------
         logger_name : str
             The name that will refer to this unique loger
         log_file: Optional[PathLike]
             The file that the log will reference
         level:
             The output level of the log, INFO, ERROR etc, which describes which what will be logged.
         Returns
         -------
        logger: Logger
             The logging object with the appropriate handlers

        """
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
        """Finds the existing logger with teh gien name or creates a new one if it doesn't exist

         Parameters
         ----------
         logger_name : str
             The name that will refer to this unique loger
         log_dir: Optional[PathLike]
             The path to file that the log will reference
         level:
             The output level of the log, INFO, ERROR etc, which describes which what will be logged.
         Returns
         -------
        logger: Logger
             The logging object with the appropriate handlers

        """
        if not logging.getLogger(log_name).hasHandlers():
            logger = WEI_Logger._create_logger(
                log_name,
                Path(log_dir) / f"{log_name}.log",
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
        """Returns a JSON blob processed from the given logs
         Parameters
         ----------
         logger_name : str
             The name that will refer to this unique loger
         log_file: Optional[PathLike]
             The file that the log will reference
         level:
             The output level of the log, INFO, ERROR etc, which describes which what will be logged.
         Returns
         -------
        logger: Logger
             The logging object with the appropriate handlers

        """

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
