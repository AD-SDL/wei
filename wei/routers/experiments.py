"""
Router for the "experiments"/"exp" endpoints
"""
from typing import Optional

from fastapi import APIRouter
from wei.core.loggers import WEI_Logger
from wei.core.experiment import (
    create_experiment,
    get_experiment_log_directory
)

router = APIRouter()


@router.post("/{experiment_id}/log")
def log_experiment(experiment_id: str, log_value: str) -> None:
    """Logs a value to the log file for a given experiment"""
    logger = WEI_Logger.get_experiment_logger(experiment_id)
    logger.info(log_value)


@router.get("/{experiment_id}/log")
async def log_return(experiment_id: str) -> str:
    """Returns the log for a given experiment"""
    with open(
        get_experiment_log_directory(experiment_id) / f"experiment_{experiment_id}.log",
        "r",
    ) as f:
        return f.read()


@router.post("/")
def process_exp(
    experiment_name: str,
    experiment_id: Optional[str] = None,
) -> dict:
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

    # Decode the bytes object to a string
    # Generate UUID for the experiment, really this should be done by the client (Experiment class)
    return create_experiment(experiment_name, experiment_id)
