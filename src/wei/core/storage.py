"""Handles all interactions with File storage/objects"""

from pathlib import Path
from typing import Optional, Union

from wei.config import Config
from wei.core.state_manager import state_manager


def initialize_storage():
    """Initializes the storage directories."""
    Config.data_directory.mkdir(parents=True, exist_ok=True)
    (Config.data_directory / "experiments").mkdir(exist_ok=True)
    (Config.data_directory / "temp").mkdir(exist_ok=True)
    (Config.data_directory / "workcells").mkdir(exist_ok=True)
    (Config.data_directory / "modules").mkdir(exist_ok=True)


def get_workcell_directory(workcell_id: str) -> Path:
    """Returns the directory for the given workcell name."""
    workcell = state_manager.get_workcell()
    return Config.data_directory / "workcells" / f"{workcell.name}_id_{workcell_id}"


def get_workcell_log_path(workcell_id: str) -> Path:
    """Returns the log file for the given workcell id."""
    return get_workcell_directory(workcell_id) / f"{workcell_id}.log"


def get_experiments_directory() -> Path:
    """Returns the directory where the experiments are stored."""
    return Config.data_directory / "experiments"


def get_experiment_directory(
    experiment_id: str, experiment_name: Optional[str] = None, create: bool = False
) -> Path:
    """Returns the directory for the given experiment id."""
    if not create:
        try:
            try:
                # Check to see if we have a cached version of the experiment
                experiment = state_manager.get_experiment(experiment_id)
                experiment_name = experiment.experiment_name
                if experiment.experiment_directory is not None:
                    # If the cached version has a saved directory, return it
                    return Path(experiment.experiment_directory)
            except Exception:
                # No cached version, so search the disk
                return search_for_experiment_directory(experiment_id)
        except Exception:
            # If we can't find the experiment directory, we'll create it at the default
            pass
    experiment_dir = (
        get_experiments_directory() / f"{experiment_name}_id_{experiment_id}"
    )
    experiment_dir.mkdir(parents=True, exist_ok=True)
    return experiment_dir


def search_for_experiment_directory(experiment_id: str) -> Path:
    """Searches for the directory for the given experiment id."""
    for directory in get_experiments_directory().iterdir():
        if directory.match(f"*{experiment_id}*"):
            return directory
    raise ValueError(f"Experiment {experiment_id} not found.")


def get_experiment_log_file(
    experiment_id: str, experiment_name: Optional[str] = None
) -> Path:
    """Returns the log file for the given experiment id."""
    return (
        get_experiment_directory(
            experiment_id=experiment_id, experiment_name=experiment_name
        )
        / f"{experiment_id}.log"
    )


def get_workflow_run_directory(
    workflow_run_id: str,
    experiment_id: Optional[str] = None,
    experiment_name: Optional[str] = None,
    workflow_name: Optional[str] = None,
) -> Path:
    """Returns the directory for the given workflow id."""
    if workflow_name is None or experiment_id is None:
        wf_run = state_manager.get_workflow_run(workflow_run_id)
        workflow_name = wf_run.name
        experiment_id = wf_run.experiment_id
    return (
        get_experiment_directory(
            experiment_id=experiment_id, experiment_name=experiment_name
        )
        / f"{workflow_name}_id_{workflow_run_id}"
    )


def get_workflow_run_log_path(
    workflow_run_id: str,
    workflow_name: Optional[str] = None,
    experiment_id: Optional[str] = None,
    experiment_name: Optional[str] = None,
) -> Path:
    """Returns the log file for the given workflow id."""
    return (
        get_workflow_run_directory(
            workflow_run_id=workflow_run_id,
            workflow_name=workflow_name,
            experiment_id=experiment_id,
            experiment_name=experiment_name,
        )
        / f"{workflow_run_id}.log"
    )


def get_module_directory(
    alias: str,
    data_directory: Optional[Union[Path, str]] = None,
):
    """Returns the directory for the given module."""
    if data_directory is None:
        data_directory = Config.data_directory
    module_dir = Path(data_directory) / "modules" / alias
    module_dir.mkdir(parents=True, exist_ok=True)
    return module_dir
