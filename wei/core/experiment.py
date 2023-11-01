"""Code for managing the Experiment logs on the server side"""

from typing import Optional

from wei.core import DATA_DIR
from wei.core.events import Events


def create_experiment(
    experiment_name,
    experiment_id: Optional[str] = None,
    kafka_server: str = None,
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
    events = Events(
        "localhost",
        "8000",
        experiment_name,
        experiment_id,
        kafka_server=kafka_server,
    )
    log_dir = DATA_DIR / (str(experiment_name) + "_id_" + experiment_id)
    runs_dir = log_dir / "runs"
    result_dir = log_dir / "results"
    log_dir.mkdir(parents=True, exist_ok=True)
    result_dir.mkdir(parents=True, exist_ok=True)
    runs_dir.mkdir(parents=True, exist_ok=True)
    events.start_experiment(log_dir)
    return {"exp_dir": log_dir}
