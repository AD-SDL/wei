"""Code for managing the Experiment logs on the server side"""

from typing import Optional

from wei.config import Config
from wei.core.data_classes import Experiment, get_experiment_name
from wei.core.events import Events
from wei.core.loggers import WEI_Logger


def get_experiment_event_server(experiment_id: str) -> Events:
    """Returns the event server for a given experiment"""
    return Events(
        Config.server_host, Config.server_port, experiment_id, wei_internal=True
    )


def get_experiment_log_directory(
    experiment_id: str,
):
    return (
        Config.data_directory
        / "experiment"
        / (str(get_experiment_name(experiment_id)) + "_id_" + experiment_id)
    )


def create_experiment(
    experiment_name: str,
    experiment_id: Optional[str] = None,
) -> dict:
    """Create the files for logging and results of the system and log the start of the Experiment


    Parameters
    ----------
    experiment_name : str
        The user-created name of the experiment

    value:  ulid, str
        the auto-created ulid of the experiment

    Returns
    -------
    Dict
       A dictionary with the experiment log_dir value"""

    if experiment_id is None:
        experiment = Experiment(experiment_name=experiment_name)
    else:
        experiment = Experiment(
            experiment_name=experiment_name, experiment_id=experiment_id
        )
    experiment.experiment_dir.mkdir(parents=True, exist_ok=True)
    experiment.run_dir.mkdir(parents=True, exist_ok=True)

    events = Events(
        Config.server_host, Config.server_port, experiment_id, wei_internal=True
    )
    events.start_experiment(experiment.experiment_dir)
    return {"exp_dir": experiment.experiment_dir}


def log_experiment_event(experiment_id: str, log_value: str) -> None:
    """Logs a value to the log file for a given experiment"""
    logger = WEI_Logger.get_experiment_logger(experiment_id)
    logger.info(log_value)
