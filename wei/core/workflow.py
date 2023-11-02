"""The module that initializes and runs the step by step WEI workflow"""
import logging
from multiprocessing.connection import Connection
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import requests
import ulid
from devtools import debug

from wei.core.config import Config
from wei.core.data_classes import (
    Module,
    PathLike,
    Step,
    StepStatus,
    WorkcellData,
    Workflow,
    WorkflowRun,
)
from wei.core.interface import InterfaceMap
from wei.core.loggers import WEI_Logger
from wei.core.modules import validate_module_names
from wei.core.state_manager import StateManager
from wei.core.workcell import find_step_module

state_manager = Config.state_manager


def workflow_logger(workflow_run: WorkflowRun):
    return WEI_Logger.get_logger(
        f"{workflow_run.run_id}_run_log", log_dir=workflow_run.run_dir
    )


def check_step(exp_id, run_id, step: dict) -> bool:
    """Check if a step is valid."""
    if "target" in step.locations:
        location = state_manager.get_location(step.locations["target"])
        if not (location.state == "Empty") or not (
            (len(location.queue) > 0 and location.queue[0] == str(run_id))
        ):
            return False

    if "source" in step.locations:
        location = state_manager.get_location(step.locations["source"])
        if not (location.state == str(exp_id)):
            return False
    module_data = state_manager.get_module(step.module)
    if not ("BUSY" in module_data.state) and not (
        (len(module_data.queue) > 0 and module_data.queue[0] == str(run_id))
    ):
        return False
    return True


def run_step(
    wf_run: WorkflowRun,
    module: Module,
    pipe: Connection,
) -> None:
    """Runs a single Step from a given workflow on a specified Module."""
    logger = workflow_logger(wf_run)  # TODO
    step: Step = wf_run.steps[wf_run.step_index]

    logger.info(f"Started running step with name: {step.name}")
    logger.debug(step)

    interface = "simulate_callback" if wf_run.simulate else module.interface

    try:
        action_response, action_msg, action_log = InterfaceMap.interfaces[
            interface
        ].send_action(step, step_module=module, experiment_path=wf_run.experiment_path)
    except Exception as e:
        logger.info(f"Exception occurred while running step with name: {step.name}")
        logger.debug(str(e))
        action_response = StepStatus.FAILED
        action_msg = "Exception occurred while running step"
        action_log = str(e)
    else:
        logger.info(f"Finished running step with name: {step.name}")

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

    validate_module_names(workflow, workcell)

    wf_run = WorkflowRun(
        **workflow.model_dump(mode="python").update(
            {
                "label": workflow.name,
                "payload": payload,
                "experiment_id": Path(experiment_path).name.split("_id_")[-1],
                "experiment_path": str(experiment_path),
                "simulate": simulate,
            }
        )
    )
    wf_run.run_dir.mkdir(parents=True, exist_ok=True)
    wf_run.result_dir.mkdir(parents=True, exist_ok=True)

    steps = []
    for step in workflow.flowdef:
        replace_positions(workcell, step)
        inject_payload(payload, step)
        steps.append(step)

    wf_run.steps = steps

    return wf_run


def replace_positions(workcell, step):
    """Replaces the positions in the step with the actual positions from the workcell"""
    if isinstance(step.args, dict) and len(step.args) > 0 and workcell.locations:
        if step.module in workcell.locations.keys():
            for key, value in step.args.items():
                # if hasattr(value, "__contains__") and "positions" in value:
                if str(value) in workcell.locations[step.module].keys():
                    step.locations[key] = value


def inject_payload(payload, step):
    """Injects the payload into the step args"""
    if len(step.args) > 0:
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
