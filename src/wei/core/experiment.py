"""Code for managing the Experiment logs on the server side"""

import os
import re
from pathlib import Path

from wei.core.state_manager import state_manager
from wei.core.storage import (
    get_experiment_directory,
    get_experiments_directory,
    search_for_experiment_directory,
)
from wei.types.experiment_types import Campaign, Experiment, ExperimentDesign
from wei.utils import threaded_task


def register_new_experiment(experiment_design: ExperimentDesign) -> Experiment:
    """Creates a new experiment, optionally associating it with a campaign"""
    new_experiment = Experiment.model_validate(experiment_design, from_attributes=True)
    # Create the experiment (sub)director(ies) if they don't exist
    new_experiment.experiment_directory = get_experiment_directory(
        new_experiment.experiment_id, new_experiment.experiment_name, create=True
    )
    # If a campaign is specified, check if it exists, and register the experiment
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

        with state_manager.campaign_lock(new_experiment.campaign_id):
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
        # Experiment not cached, so search the disk
        experiment = Experiment(
            experiment_id=experiment_id,
            experiment_name=search_for_experiment_directory(experiment_id).split(
                "_id_"
            )[0],
        )
    return experiment


@threaded_task
def parse_experiments_from_disk():
    """Scans the experiments directory and pulls in any experiments that are not in the state_manager."""
    experiments_dir = get_experiments_directory()
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
            # Experiment already in state_manager, so skip it
            continue
        except KeyError:
            experiment_name = regex_match[1]
            experiment = Experiment(
                experiment_id=experiment_id,
                experiment_name=experiment_name,
                experiment_directory=str(
                    get_experiments_directory() / Path(experiment_dir)
                ),
            )
            state_manager.set_experiment(experiment)
        except Exception:
            continue
