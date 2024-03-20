"""
Router for the "experiments"/"exp" endpoints
"""

import json
from typing import Dict, Optional

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from wei.core.experiment import Experiment, list_experiments
from wei.core.state_manager import StateManager

router = APIRouter()

state_manager = StateManager()


@router.get("/{experiment_id}/log")
async def log_return(experiment_id: str) -> str:
    """Returns the log for a given experiment"""
    experiment = Experiment(experiment_id=experiment_id)

    with open(
        experiment.experiment_log_file,
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


@router.get("/all")
async def get_all_experiments() -> Dict[str, str]:
    """Returns all experiments inside DataFolder"""
    return list_experiments()


@router.get("/")
def register_experiment(
    experiment_name: str,
    experiment_id: Optional[str] = None,
) -> Dict[str, str]:
    """Pulls an experiment and creates the files and logger for it

    Parameters
    ----------
    experiment_name: str
        The human created name of the experiment
    experiment_id : str
       The programmatically generated id of the experiment for the workflow
    Returns
    -------
     response: Dict
       a dictionary including the successfulness of the queueing, the jobs ahead and the id

    """

    experiment = Experiment(
        experiment_name=experiment_name, experiment_id=experiment_id
    )
    experiment.experiment_dir.mkdir(parents=True, exist_ok=True)
    experiment.run_dir.mkdir(parents=True, exist_ok=True)

    return {
        "experiment_id": experiment.experiment_id,
        "experiment_name": experiment.experiment_name,
        "experiment_path": str(experiment.experiment_dir),
    }
