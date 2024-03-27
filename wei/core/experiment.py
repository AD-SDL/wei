"""Code for managing the Experiment logs on the server side"""

import os
import re
from pathlib import Path
from typing import Optional

from wei.config import Config
from wei.core.state_manager import StateManager
from wei.types.experiment_types import Campaign, Experiment, ExperimentDesign

state_manager = StateManager()


def register_new_experiment(experiment_design: ExperimentDesign) -> Experiment:
    """Creates a new experiment, optionally associating it with a campaign"""
    new_experiment = Experiment.model_validate(experiment_design, from_attributes=True)
    print(new_experiment.model_dump_json())
    get_experiment_dir(
        new_experiment.experiment_id, new_experiment.experiment_name
    ).mkdir(parents=True, exist_ok=True)
    get_experiment_runs_dir(
        new_experiment.experiment_id, new_experiment.experiment_name
    ).mkdir(parents=True, exist_ok=True)
    with state_manager.lab_state_lock():
        if new_experiment.campaign_id is not None:
            try:
                state_manager.get_campaign(new_experiment.campaign_id)
            except KeyError as e:
                raise ValueError(
                    f"Campaign {new_experiment.campaign_id} not found, please create it first (this only needs to be done once)."
                ) from e

            def append_experiment_id_to_campaign(
                campaign: Campaign, experiment_id: str
            ) -> Campaign:
                campaign.experiment_ids.append(experiment_id)
                return campaign

            state_manager.update_campaign(
                new_experiment.campaign_id,
                append_experiment_id_to_campaign,
                new_experiment.experiment_id,
            )
        state_manager.set_experiment(new_experiment)
    return new_experiment


def get_experiment(experiment_id: str) -> Experiment:
    """Returns the experiment details"""
    try:
        experiment = state_manager.get_experiment(experiment_id)
    except KeyError:
        experiment = get_experiment_from_disk(experiment_id)
    return experiment


def get_experiment_from_disk(experiment_id: str) -> Experiment:
    """Returns the experiment details from the disk"""
    experiment_data = Experiment(
        experiment_id=experiment_id,
        experiment_name=get_experiment_name_from_disk(experiment_id),
    )
    return experiment_data


def get_experiment_dir_from_disk(experiment_id: str) -> Path:
    """Returns the experiment directory from the experiment_id, only looking on disk."""
    for directory in Path(get_experiments_dir()).iterdir():
        if directory.match(f"*{experiment_id}*"):
            return directory
    return None


def get_experiment_name_from_disk(experiment_id: str) -> str:
    """Returns the name of the experiment using the experiment_id, only looking on disk."""
    experiment_dir = get_experiment_dir_from_disk(experiment_id).split("_id_")[0]
    if experiment_dir is None:
        raise ValueError(f"Experiment {experiment_id} not found on disk")


def get_experiments_dir() -> Path:
    """Returns the directory where the experiments are stored"""
    return Config.data_directory / "experiments"


def get_experiment_log_file(experiment_id: str) -> Path:
    """Returns the experiment's log file"""
    return get_experiment_dir(experiment_id) / f"experiment_{experiment_id}.log"


def get_experiment_runs_dir(
    experiment_id: str, experiment_name: Optional[str] = None
) -> Path:
    """Returns the run directory for the experiment"""
    return get_experiment_dir(experiment_id, experiment_name) / "runs"


def get_experiment_dir(
    experiment_id: str, experiment_name: Optional[str] = None
) -> Path:
    """Returns the experiment directory from the experiment_id"""
    if experiment_name is None:
        try:
            state_manager.get_experiment(experiment_id)
            return get_experiments_dir() / f"{experiment_id}_id_{experiment_id}"
        except KeyError:
            get_experiment_dir_from_disk(experiment_id)
    else:
        return get_experiments_dir() / f"{experiment_name}_id_{experiment_id}"


def parse_experiments_from_disk():
    """Scans the experiments directory and pulls in any experiments that are not in the state_manager."""
    experiments_dir = get_experiments_dir()
    subdirs = os.listdir(experiments_dir)
    experiment_dir_pattern = r"(.+)_id_(.+)"
    for experiment_dir in subdirs:
        regex_match = re.match(experiment_dir_pattern, experiment_dir)
        if regex_match is None:
            # Name doesn't match the pattern, so skip it
            continue
        experiment_id = regex_match[2]
        try:
            experiment = state_manager.get_experiment(experiment_id)
            continue
        except KeyError:
            experiment_name = regex_match[1]
            # TODO: Try to extract campaign_id and data_point_definition
            experiment = Experiment(
                experiment_id=experiment_id,
                experiment_name=experiment_name,
            )
            with state_manager.lab_state_lock():
                state_manager.set_experiment(experiment)
