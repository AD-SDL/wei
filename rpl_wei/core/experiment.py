"""Code for managing the Experiment logs on the server side"""

from typing import Optional, Union

import ulid

from rpl_wei.core import DATA_DIR
from rpl_wei.core.loggers import WEI_Logger
from rpl_wei.core.events import Events

def start_experiment(
    experiment_name, experiment_id: Optional[Union[ulid.ULID, str]] = None
):
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
        "ec2-54-160-200-147.compute-1.amazonaws.com:9092",
    )

    log_dir = DATA_DIR / (str(experiment_name) + "_" + experiment_id)
    runs_dir = log_dir /"wei_runs"
    result_dir = log_dir / "results"
    log_dir.mkdir(parents=True, exist_ok=True)
    result_dir.mkdir(parents=True, exist_ok=True)
    runs_dir.mkdir(parents=True, exist_ok=True)  
    print("done")
    events.start_experiment()
    return {"exp_dir": str(log_dir)}
