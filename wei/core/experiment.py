"""Code for managing the Experiment logs on the server side"""

import fnmatch
import os
import re
from pathlib import Path
from typing import Optional

import ulid

from wei.config import Config


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
        self.experiments_dir = Config.data_directory / "experiments"
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
        try:
            return [
                filename
                for filename in os.listdir(str(self.experiments_dir))
                if fnmatch.fnmatch(filename, f"*{self.experiment_id}*")
            ][0].split("_id_")[0]
        except IndexError:
            return "Unnamed"

    @property
    def experiment_dir(self) -> Path:
        """Path to the result directory"""
        return self.experiments_dir / (
            str(self.experiment_name) + "_id_" + self.experiment_id
        )

    @property
    def experiment_log_file(self) -> Path:
        """Path to the experiment's log file"""
        return self.experiment_dir / f"experiment_{self.experiment_id}.log"

    @property
    def run_dir(self) -> Path:
        """Path to the result directory"""
        return self.experiment_dir / "runs"


def list_experiments():
    """Return a list of all experiments in the Config folger

    Returns
    -------
    all_exps Dict
    """
    experiments_dir = Config.data_directory / "experiments"
    all_exps_raw = os.listdir(experiments_dir)
    pat1 = r"(.+)_id_(.+)"
    all_exps = {}
    for exp in all_exps_raw:
        test = re.match(pat1, exp)
        all_exps[test[2]] = test[1]
    return all_exps
