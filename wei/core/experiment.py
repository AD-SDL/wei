"""Code for managing the Experiment logs on the server side"""

import fnmatch
import os
from pathlib import Path
from typing import Optional

import ulid

from wei.config import Config
from wei.core.events import Events


class Experiment:
    """Class to work with Experiment's and their logs inside WEI"""

    experiment_id: str
    experiment_name: str

    def __init__(
        self, experiment_id: Optional[str] = None, experiment_name: Optional[str] = None
    ):
        """Initialize the Experiment class

        Parameters
        ----------
        experiment_id : str
            The unique id of the experiment
                - If not provided, will be auto-generated
        experiment_name : str
            The user-created name of the experiment
                - If not provided, will be looked up using the experiment_id
                - Must be provided if the experiment_dir is not yet created
        """
        if experiment_id is None:
            self.experiment_id = ulid.new().str
        else:
            self.experiment_id = experiment_id
        if experiment_name is None:
            self.experiment_name = self.get_experiment_name()
        else:
            self.experiment_name = experiment_name

    def get_experiment_name(self) -> str:
        """Returns the name of the experiment using the experiment_id"""
        data_dir = str(Config.data_directory)
        return [
            filename
            for filename in os.listdir(str(data_dir) + "/experiment")
            if fnmatch.fnmatch(filename, f"*{self.experiment_id}*")
        ][0]

    @property
    def experiment_dir(self) -> Path:
        """Path to the result directory"""
        return (
            Config.data_directory
            / "experiment"
            / (str(self.experiment_name) + "_id_" + self.experiment_id)
        )

    @property
    def experiment_log_file(self) -> Path:
        """Path to the experiment's log file"""
        return self.experiment_dir / f"experiment_{self.experiment_id}.log"

    @property
    def run_dir(self) -> Path:
        """Path to the result directory"""
        return self.experiment_dir / "runs"


def get_experiment_event_server(experiment_id: str) -> Events:
    """Returns the event server for a given experiment"""
    return Events(
        Config.server_host, str(Config.server_port), experiment_id, wei_internal=True
    )


def get_experiment_log_directory(
    experiment_id: str,
) -> Path:
    """Returns the path to an experiment's log directory"""
    return (
        Config.data_directory
        / "experiment"
        / (str(Experiment(experiment_id).experiment_name) + "_id_" + experiment_id)
    )


def create_experiment(
    experiment_name: str,
    experiment_id: Optional[str] = None,
) -> dict[str, Path]:
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

    get_experiment_event_server(experiment.experiment_id).start_experiment()
    return {"exp_dir": experiment.experiment_dir}
