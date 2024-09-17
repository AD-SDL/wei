"""
Router for the "experiments"/"exp" endpoints
"""

import json
from datetime import datetime
from typing import Dict

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from wei.core.experiment import get_experiment, register_new_experiment
from wei.core.state_manager import state_manager
from wei.core.storage import get_experiment_log_file
from wei.types.datapoint_types import DataPoint
from wei.types.event_types import Event
from wei.types.experiment_types import Experiment, ExperimentDesign

router = APIRouter()


@router.get("/{experiment_id}/events")
async def event_return(experiment_id: str) -> Dict[str, Event]:
    """Returns all of the saved events related to an experiment"""
    events = {}
    for event_id, event in state_manager.get_all_events().items():
        if event.experiment_id == experiment_id:
            events[event_id] = event
    return events


@router.post("/{experiment_id}/check_in")
async def check_in(experiment_id: str) -> None:
    """Returns a simple pong response"""
    experiment = state_manager.get_experiment(experiment_id)
    experiment.check_in_timestamp = datetime.now()
    with state_manager.wc_state_lock():
        state_manager.set_experiment(experiment)

    return


@router.get("/{experiment_id}/data")
async def data_return(experiment_id: str) -> Dict[str, DataPoint]:
    """Returns all of the data points related to an experiment"""
    datapoints = {}
    for datapoint_id, datapoint in state_manager.get_all_datapoints().items():
        if datapoint.experiment_id == experiment_id:
            datapoints[datapoint_id] = datapoint
    return datapoints


@router.get("/{experiment_id}/log")
async def log_return(experiment_id: str) -> str:
    """Returns the log for a given experiment"""
    try:
        experiment_log = get_experiment_log_file(experiment_id)
        if experiment_log.exists():
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
        else:
            return JSONResponse({"error": "Log file not found"}, status_code=404)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
    return JSONResponse(logs)


@router.get("/")
@router.get("/all")
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
