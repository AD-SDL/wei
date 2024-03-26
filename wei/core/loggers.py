"""The logging system that helps track events for the system"""

import logging
from pathlib import Path

from wei.config import Config
from wei.core.experiment import get_experiment_dir
from wei.types.base_types import PathLike
from wei.types.workflow_types import WorkflowRun


def get_workflow_run_dir(wf_run: WorkflowRun) -> Path:
    """Returns the directory of the workflow run"""
    return Path(
        get_experiment_dir(wf_run.experiment_id) / f"{wf_run.name}_{wf_run.run_id}"
    )


def get_workflow_run_log_path(wf_run: WorkflowRun) -> Path:
    """Returns the log file of the workflow run"""
    return Path(
        get_workflow_run_dir(wf_run),
        wf_run.run_id + "_run_log.log",
    )


def get_workflow_run_result_dir(wf_run: WorkflowRun) -> str:
    """Returns the result directory of the workflow run"""
    return get_workflow_run_dir(wf_run) / "results"


class Logger:
    """The logging system that helps track events for the system"""

    @staticmethod
    def _create_logger(
        logger_name: str,
        log_file: PathLike,
        level: int = logging.INFO,
    ) -> logging.Logger:
        """Creates a logger that attaches to the given file

         Parameters
         ----------
         logger_name : str
             The name that will refer to this unique logger
         log_file: Optional[PathLike]
             The file that the log will reference
         level:
             The output level of the log, INFO, ERROR etc, which describes which what will be logged.
         Returns
         -------
        logger: Logger
             The logging object with the appropriate handlers
        """

        Path(log_file).parent.mkdir(parents=True, exist_ok=True)

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
    def get_lab_logger() -> logging.Logger:
        """Finds the existing logger with the given name or creates a new one if it doesn't exist

        Returns
        -------
        logger: Logger
            The logging object with the appropriate handlers
        """
        return Logger.get_logger(
            f"{Config.lab_name}",
            Config.data_directory,
            log_level=Config.log_level,
        )

    @staticmethod
    def get_workcell_logger(workcell_id: str) -> logging.Logger:
        """Finds the existing logger with the given name or creates a new one if it doesn't exist

        Parameters
        ----------
        workcell_id : str
            The id of the workcell that will refer to this unique logger
        Returns
        -------
        logger: Logger
            The logging object with the appropriate handlers
        """
        from wei.core.workcell import get_workcell_dir

        return Logger.get_logger(
            f"{workcell_id}",
            get_workcell_dir(workcell_id),
            log_level=Config.log_level,
        )

    @staticmethod
    def get_experiment_logger(
        experiment_id: str,
    ) -> logging.Logger:
        """Finds the existing logger with the given name or creates a new one if it doesn't exist

        Parameters
        ----------
        experiment_id : str
            The id of the experiment that will refer to this unique logger
        Returns
        -------
        logger: Logger
            The logging object with the appropriate handlers
        """
        from wei.core.experiment import get_experiment_dir

        return Logger.get_logger(
            f"experiment_{experiment_id}",
            get_experiment_dir(experiment_id),
            log_level=Config.log_level,
        )

    @staticmethod
    def get_workflow_run_logger(wf_run: WorkflowRun) -> logging.Logger:
        """Finds the existing logger with the given name or creates a new one if it doesn't exist

        Parameters
        ----------
        run_id : str
            The id of the workflow run that will refer to this unique logger
        Returns
        -------
        logger: Logger
            The logging object with the appropriate handlers
        """

        return Logger.get_logger(
            f"{wf_run.run_id}_run_log",
            get_workflow_run_dir(wf_run),
            log_level=Config.log_level,
        )

    @staticmethod
    def get_logger(
        log_name: str,
        log_dir: PathLike,
        log_level: int = logging.INFO,
    ) -> logging.Logger:
        """Finds the existing logger with the given name or creates a new one if it doesn't exist

        Parameters
        ----------
        logger_name : str
            The name that will refer to this unique logger
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
            logger = Logger._create_logger(
                log_name,
                Path(log_dir) / f"{log_name}.log",
                log_level,
            )
        else:
            logger = logging.getLogger(log_name)
            while not (logger.handlers == []):
                for handler in logger.handlers:
                    logger.removeHandler(handler)

            log_file = Path(log_dir) / f"{log_name}.log"
            log_file.parent.mkdir(parents=True, exist_ok=True)
            formatter = logging.Formatter("%(asctime)s (%(levelname)s): %(message)s")
            fileHandler = logging.FileHandler(log_file, mode="a+")
            fileHandler.setFormatter(formatter)
            streamHandler = logging.StreamHandler()
            streamHandler.setFormatter(formatter)

            logger.setLevel(log_level)
            logger.addHandler(fileHandler)
            logger.addHandler(streamHandler)

        return logger
