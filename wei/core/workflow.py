"""The module that initializes and runs the step by step WEI workflow"""
import logging
from multiprocessing.connection import Connection
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import requests
import ulid
from devtools import debug

from wei.core.data_classes import (
    Module,
    PathLike,
    Step,
    WorkcellData,
    Workflow,
    WorkflowRun,
)
from wei.core.loggers import WEI_Logger
from wei.core.step_executor import StepExecutor
from wei.core.workcell import find_step_module
from wei.state_manager import StateManager


def workflow_logger(workflow_run: WorkflowRun):
    return (
        WEI_Logger.get_logger(
            f"{workflow_run.run_id}_run_log",
            log_dir=workflow_run.run_dir
        )
    )


def check_step(
    exp_id, run_id, step: dict, state: StateManager
) -> bool:
    """Check if a step is valid."""
    print(step)
    if "target" in step.locations:
        location = state.get_location(step.locations["target"])
        if not (location.state == "Empty") or not (
            (len(location.queue) > 0 and location.queue[0] == str(run_id))
        ):
            return False

    if "source" in step.locations:
        location = state.get_location(step.locations["source"])
        if not (location.state == str(exp_id)):
            return False
    module_data = state.get_module(step.module)
    if not ("BUSY" in module_data.state) and not (
        (len(module_data.queue) > 0 and module_data.queue[0] == str(run_id))
    ):
        return False
    return True


def run_step(
    wf_run: WorkflowRun,
    module: Module,
    pipe: Connection,
    executor: StepExecutor,
) -> None:
    """Runs a single Step from a given workflow on a specified Module."""
    logger = workflow_logger(wf_run)  # TODO
    step: Step = wf_run.steps[wf_run.step_index]
    action_response, action_msg, action_log = executor.execute_step(
        step, module, logger=logger, exp_path=wf_run.experiment_path
    )
    pipe.send(
        {
            "step_response": {
                "action_response": str(action_response),
                "action_msg": action_msg,
                "action_log": action_log,
            },
            "step": step,
            "locations": step.locations,
            "log_dir": wf_run.run_dir,
        }
    )


def create_run(
    workflow: Workflow,
    workcell: WorkcellData,
    payload: Optional[Dict[str, Any]] = None,
    experiment_path: Optional[PathLike] = None,
    simulate: bool = False,
) -> WorkflowRun:
    """Pulls the workcell and builds a list of dictionary steps to be executed

    Parameters
    ----------
    workflow: Workflow
        The workflow data file loaded in from the workflow yaml file

    workcell : Workcell
        The Workcell data file loaded in from the workcell yaml file

    payload: Dict
        The input to the workflow

    experiment_path: PathLike
        The path to the data of the experiment for the workflow

    simulate: bool
        Whether or not to use real robots

    Returns
    -------
    steps: WorkflowRun
        a completely initialized workflow run
    """
    print(workcell)
    path = Path(experiment_path)
    experiment_id = path.name.split("_id_")[-1]

    # Start executing the steps
    steps = []
    for module in workflow.modules:
        
        if not (find_step_module(workcell, module.name)):
            raise ValueError(f"Module {module} not in Workcell {workflow.modules}")
   
    kwargs =  workflow.model_dump()
    kwargs.update({"label": workflow.name,
        "payload": payload,
        "experiment_id": experiment_id,
        "experiment_path": str(experiment_path),
        "simulate": simulate})
 
    wf_run = WorkflowRun(
        **kwargs
    )
    wf_run.run_dir.mkdir(parents=True, exist_ok=True)
    wf_run.result_dir.mkdir(parents=True, exist_ok=True)
    for step in workflow.flowdef:
        # get module information from workcell file
        step_module = find_step_module(workcell, step.module)
        if not step_module:
            raise ValueError(
                f"No module found for step module: {step.module}, in step: {step}"
            )
        valid = False
        for module in workflow.modules:
            if step.module == module.name:
                valid = True
        if not (valid):
            raise ValueError(f"Module {step.module} not in flow modules")
        # replace position names with actual positions
        if isinstance(step.args, dict) and len(step.args) > 0 and workcell.locations:
            if step.module in workcell.locations.keys():
                for key, value in step.args.items():
                    # if hasattr(value, "__contains__") and "positions" in value:
                    if str(value) in workcell.locations[step.module].keys():
                        step.locations[key] = value

        # Inject the payload
        if isinstance(payload, dict):
            if not isinstance(step.args, dict) or len(step.args) == 0:
                continue
            # TODO check if you can see the attr of this class and match them with vars in the yaml
            (arg_keys, arg_values) = zip(*step.args.items())
            for key, value in payload.items():
                # Covers naming issues when referring to namespace from yaml file
                if "payload." not in key:
                    key = f"payload.{key}"
                if key in arg_values:
                    idx = arg_values.index(key)
                    step_arg_key = arg_keys[idx]
                    step.args[step_arg_key] = value
        steps.append(step)

    wf_run.steps = steps
    return wf_run
