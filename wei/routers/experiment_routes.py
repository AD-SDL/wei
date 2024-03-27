"""
Router for the "experiments"/"exp" endpoints
"""

import json
from typing import Dict

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from wei.core.experiment import (
    get_experiment,
    get_experiment_log_file,
    register_new_experiment,
)
from wei.core.state_manager import StateManager
from wei.types.experiment_types import Campaign, Experiment, ExperimentDesign

router = APIRouter()

state_manager = StateManager()


@router.get("/{experiment_id}/log")
async def log_return(experiment_id: str) -> str:
    """Returns the log for a given experiment"""
    with open(
        get_experiment_log_file(experiment_id),
        "r",
    ) as f:
        val = f.readlines()
    logs = []
    for entry in val:
        try:
            logs.append(json.loads(entry.split("(INFO):")[1].strip()))
        except Exception as e:
            print(e)
    return JSONResponse(logs)


@router.get("/")
async def get_all_experiments() -> Dict[str, Experiment]:
    """Returns all experiments inside DataFolder"""
    return state_manager.get_all_experiments()


@router.get("/{experiment_id}")
def get_experiment_endpoint(experiment_id: str) -> Experiment:
    """Returns the details for a specific experiment given the id"""
    return get_experiment(experiment_id)


@router.post("/")
def register_experiment(
    experiment_design: ExperimentDesign,
) -> Experiment:
    """Creates a new experiment, optionally associating it with a campaign"""
    return register_new_experiment(experiment_design)


@router.post("/campaign")
def register_campaign(campaign_name: str) -> Campaign:
    """Creates a new campaign

    Parameters
    ----------
    campaign_name: str
        The human readable name of the campaign
    Returns
    -------
    response: Campaign
    """

    campaign = Campaign(campaign_name=campaign_name)
    state_manager.set_campaign(campaign)
    return campaign


@router.get("/campaign/{campaign_id}")
def get_campaign(campaign_id: str) -> Campaign:
    """Returns the details of a campaign"""
    return state_manager.get_campaign(campaign_id)
