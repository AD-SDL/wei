"""
Router for the "experiments"/"exp" endpoints
"""
from pathlib import Path

from fastapi import APIRouter, Request

from wei.core.experiment import start_experiment
from wei.core.loggers import WEI_Logger

router = APIRouter()


@router.post("/{experiment_id}/log")
def log_experiment(experiment_path: str, log_value: str) -> None:
    """Logs a value to the log file for a given experiment"""
    log_dir = Path(experiment_path)
    experiment_id = log_dir.name.split("_id_")[-1]
    logger = WEI_Logger.get_logger("log_" + experiment_id, log_dir)
    logger.info(log_value)


@router.get("/{experiment_id}/log")
async def log_return(experiment_path: str) -> str:
    """Returns the log for a given experiment"""
    log_dir = Path(experiment_path)
    experiment_id = log_dir.name.split("_")[-1]
    with open(log_dir / Path("log_" + experiment_id + ".log"), "r") as f:
        return f.read()


@router.post("/")
def process_exp(experiment_name: str, experiment_id: str, request: Request) -> dict:
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
    return start_experiment(experiment_name, experiment_id, request.app.kafka_server)
