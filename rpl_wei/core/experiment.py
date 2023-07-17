"""Code for managing the Experiment logs on the server side"""

from typing import Optional, Union

import ulid

from rpl_wei.core import DATA_DIR
from rpl_wei.core.events import Events


def start_experiment(
    experiment_name, experiment_id: Optional[Union[ulid.ULID, str]] = None, kakfa_server: str = None
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
        kafka_server=kakfa_server,
    )
    print(experiment_name)
    print(experiment_id)
    log_dir = DATA_DIR / (str(experiment_name) + "_id_" + experiment_id)
    runs_dir = log_dir / "wei_runs"
    result_dir = log_dir / "results"
    log_dir.mkdir(parents=True, exist_ok=True)
    result_dir.mkdir(parents=True, exist_ok=True)
    runs_dir.mkdir(parents=True, exist_ok=True)
    print("done")
    events.start_experiment(log_dir)
    return {"exp_dir": log_dir}
