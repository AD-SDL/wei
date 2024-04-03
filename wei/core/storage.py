"""Handles all interactions with File storage/objects"""

from pathlib import Path
from typing import Optional

from wei.config import Config
from wei.core.state_manager import StateManager

state_manager = StateManager()


def get_workcell_directory(workcell_id: str) -> Path:
    """Returns the directory for the given workcell name."""
    workcell = state_manager.get_workcell()
    return Config.data_directory / "workcells" / f"{workcell.name}_id_{workcell_id}"


def get_workcell_run_log_path(workcell_id: str) -> Path:
    """Returns the log file for the given workcell id."""
    return get_workcell_directory(workcell_id) / f"{workcell_id}.log"


def get_experiments_directory() -> Path:
    """Returns the directory where the experiments are stored."""
    return Config.data_directory / "experiments"


def get_experiment_directory(
    experiment_id: str, experiment_name: Optional[str] = None
) -> Path:
    """Returns the directory for the given experiment id."""
    if experiment_name is None:
        try:
            experiment_name = state_manager.get_experiment(
                experiment_id
            ).experiment_name
        except KeyError:
            return search_for_experiment_directory(experiment_id)
    return get_experiments_directory() / f"{experiment_name}_id_{experiment_id}"


def search_for_experiment_directory(experiment_id: str) -> Path:
    """Searches for the directory for the given experiment id."""
    for directory in get_experiments_directory().iterdir():
        if directory.match(f"*{experiment_id}*"):
            return directory
    raise ValueError(f"Experiment {experiment_id} not found.")


def get_experiment_log_file(experiment_id: str) -> Path:
    """Returns the log file for the given experiment id."""
    return (
        get_experiment_directory(experiment_id=experiment_id) / f"{experiment_id}.log"
    )


def get_experiment_workflows_directory(
    experiment_id: str, experiment_name: Optional[str] = None
) -> Path:
    """Returns the directory for the given experiment id."""
    return (
        get_experiment_directory(
            experiment_id=experiment_id, experiment_name=experiment_name
        )
        / "workflows"
    )


def get_workflow_run_directory(
    workflow_run_id: str,
    experiment_id: Optional[str] = None,
    workflow_name: Optional[str] = None,
) -> Path:
    """Returns the directory for the given workflow id."""
    if workflow_name is None or experiment_id is None:
        wf_run = state_manager.get_workflow_run(workflow_run_id)
        workflow_name = wf_run.name
        experiment_id = wf_run.experiment_id
    return (
        get_experiment_directory(experiment_id=experiment_id)
        / "workflows"
        / f"{workflow_name}_id_{workflow_run_id}"
    )


def get_workflow_result_directory(
    workflow_run_id: str,
    workflow_name: Optional[str] = None,
    experiment_id: Optional[str] = None,
) -> Path:
    """Returns the directory for the given workflow id."""
    return (
        get_workflow_run_directory(
            workflow_run_id=workflow_run_id,
            workflow_name=workflow_name,
            experiment_id=experiment_id,
        )
        / "results"
    )


def get_workflow_run_log_path(workflow_run_id: str) -> Path:
    """Returns the log file for the given workflow id."""
    return (
        get_workflow_run_directory(workflow_run_id=workflow_run_id)
        / f"{workflow_run_id}.log"
    )
