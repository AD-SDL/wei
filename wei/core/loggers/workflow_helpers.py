"""This module contains helper functions for log files of workflow runs"""

from pathlib import Path

from wei.core.experiment import get_experiment_dir
from wei.types import WorkflowRun


def get_workflow_run_dir(wf_run: WorkflowRun) -> Path:
    """Returns the directory of the workflow run"""
    return Path(
        get_experiment_dir(wf_run.experiment_id) / f"{wf_run.name}_{wf_run.run_id}"
    )


def get_workflow_run_log_path(wf_run: WorkflowRun) -> Path:
    """Returns the log file of the workflow run"""
    return Path(
        get_workflow_run_dir(wf_run),
        wf_run.run_id + "_run_log.log",
    )


def get_workflow_run_result_dir(wf_run: WorkflowRun) -> str:
    """Returns the result directory of the workflow run"""
    return get_workflow_run_dir(wf_run) / "results"
