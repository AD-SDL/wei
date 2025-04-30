"""The module that initializes and runs the step by step WEI workflow"""

import copy
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import UploadFile

from wei.core.events import send_event
from wei.core.location import free_source_and_target
from wei.core.module import clear_module_reservation, validate_module_names
from wei.core.state_manager import state_manager
from wei.core.step import validate_step
from wei.core.storage import get_workflow_run_directory
from wei.core.workcell import find_step_module
from wei.core.workflow_admin import wf_status_change
from wei.types import Step, Workcell, Workflow, WorkflowRun
from wei.types.event_types import WorkflowCancelled
from wei.types.workflow_types import WorkflowStatus


def create_run(
    workflow: Workflow,
    workcell: Workcell,
    experiment_id: str,
    payload: Optional[Dict[str, Any]] = None,
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
    validate_module_names(workflow, workcell)
    wf_dict = workflow.model_dump()
    wf_dict.update(
        {
            "label": workflow.name,
            "payload": payload,
            "experiment_id": experiment_id,
            "simulate": simulate,
        }
    )
    wf_run = WorkflowRun(**wf_dict)

    steps = []
    for step in workflow.flowdef:
        if payload:
            inject_payload(payload, step)
        replace_positions(workcell, step)
        valid, validation_string = validate_step(step)
        print(validation_string)
        if not valid:
            raise ValueError(validation_string)
        steps.append(step)

    wf_run.steps = steps

    return wf_run


def replace_positions(workcell: Workcell, step: Step) -> None:
    """Replaces the positions in the step with the actual positions from the workcell"""
    for key, value in step.args.items():
        try:
            if str(value) in workcell.locations[step.module].keys():
                step.args[key] = workcell.locations[step.module][value]
                step.locations[key] = value
        except Exception as _:
            continue


def inject_payload(payload: Dict[str, Any], step: Step) -> None:
    """Injects the payload into the step args"""
    if len(step.args) > 0:
        # TODO check if you can see the attr of this class and match them with vars in the yaml
        (arg_keys, arg_values) = zip(*step.args.items())
        for key, value in payload.items():
            # Covers naming issues when referring to namespace from yaml file
            if not key.startswith("payload."):
                key = f"payload.{key}"
            if key in arg_values:
                idx = arg_values.index(key)
                step_arg_key = arg_keys[idx]
                step.args[step_arg_key] = value


def save_workflow_files(wf_run: WorkflowRun, files: List[UploadFile]) -> WorkflowRun:
    """Saves the files to the workflow run directory,
    and updates the step files to point to the new location"""

    get_workflow_run_directory(
        workflow_name=wf_run.name,
        workflow_run_id=wf_run.run_id,
        experiment_id=wf_run.experiment_id,
    ).mkdir(parents=True, exist_ok=True)
    if files:
        for file in files:
            file_path = (
                get_workflow_run_directory(
                    workflow_run_id=wf_run.run_id,
                    workflow_name=wf_run.name,
                    experiment_id=wf_run.experiment_id,
                )
                / file.filename
            )
            with open(file_path, "wb") as f:
                f.write(file.file.read())
            for step in wf_run.steps:
                for step_file_key, step_file_path in step.files.items():
                    if step_file_path == file.filename:
                        step.files[step_file_key] = str(file_path)
                        print(f"{step_file_key}: {file_path} ({step_file_path})")
    return wf_run


def pause_workflow_run(wf_run: WorkflowRun) -> None:
    """Pauses the workflow run"""
    wf_status_change.set()
    wf_run.status = WorkflowStatus.PAUSED
    with state_manager.wc_state_lock():
        state_manager.set_workflow_run(wf_run)
    return wf_run


def resume_workflow_run(wf_run: WorkflowRun) -> None:
    """Resumes the workflow run"""
    wf_run.status = WorkflowStatus.IN_PROGRESS
    with state_manager.wc_state_lock():
        state_manager.set_workflow_run(wf_run)
    return wf_run


def cancel_workflow_run(wf_run: WorkflowRun) -> None:
    """Cancels the workflow run"""
    wf_status_change.set()
    wf_run.status = WorkflowStatus.CANCELLED
    wf_run.end_time = datetime.now()

    if wf_run.start_time is None:
        wf_run.start_time = wf_run.end_time
    wf_run.duration = wf_run.end_time - wf_run.start_time

    step = wf_run.steps[wf_run.step_index]
    module = find_step_module(state_manager.get_workcell(), step.module)

    with state_manager.wc_state_lock():
        clear_module_reservation(module)
        free_source_and_target(wf_run)
        state_manager.set_workflow_run(wf_run)

    send_event(WorkflowCancelled.from_wf_run(wf_run=wf_run))
    print(f"Workflow run with id {wf_run.run_id} has been cancelled.")

    return wf_run


def cancel_active_workflow_runs() -> None:
    """Cancels all currently running workflow runs"""
    for wf_run in state_manager.get_all_workflow_runs().values():
        if wf_run.status in [
            WorkflowStatus.RUNNING,
            WorkflowStatus.QUEUED,
            WorkflowStatus.IN_PROGRESS,
        ]:
            cancel_workflow_run(wf_run)


def insert_parameter_values(workflow: Workflow, parameters: Dict[str, Any]):
    """Replace the parameter strings in the workflow with the provided values"""
    for param in workflow.parameters:
        if param.name not in parameters.keys():
            if param.default:
                parameters[param.name] = param.default
            else:
                raise ValueError(
                    "Workflow parameter: "
                    + param.name
                    + " not provided, and no default value is defined."
                )
    steps = []
    for step in workflow.flowdef:
        for key, val in iter(step):
            if type(val) is str:
                setattr(step, key, value_substitution(val, parameters))

        step.args = walk_and_replace(step.args, parameters)
        steps.append(step)
    workflow.flowdef = steps


def walk_and_replace(args: Dict[str, Any], input_parameters: Dict[str, Any]):
    """Recursively walk the arguments and replace all parameters"""
    new_args = copy.deepcopy(args)
    for key in args.keys():
        if type(args[key]) is str:
            new_args[key] = value_substitution(args[key], input_parameters)
        elif type(args[key]) is dict:
            new_args[key] = walk_and_replace(args[key], input_parameters)
        if type(key) is str:
            new_key = value_substitution(key, input_parameters)
            new_args[new_key] = new_args[key]
            if key is not new_key:
                new_args.pop(key, None)
    return new_args


def value_substitution(input_string: str, input_parameters: Dict[str, Any]):
    """Perform $-string substitution on input string, returns string with substituted values"""
    # * Check if the string is a simple parameter reference
    if type(input_string) is str and re.match(r"^\$[A-z0-9_\-]*$", input_string):
        if input_string.strip("$") in input_parameters.keys():
            input_string = input_parameters[input_string.strip("$")]
        else:
            raise ValueError(
                "Unknown parameter:"
                + input_string
                + ", please define it in the parameters section of the Workflow Definition."
            )
    else:
        # * Replace all parameter references contained in the string
        working_string = input_string
        for match in re.findall(r"((?<!\$)\$(?!\$)[A-z0-9_\-\{]*)(\})", input_string):
            if match[0][1] == "{":
                param_name = match[0].strip("$")
                param_name = param_name.strip("{")
                working_string = re.sub(
                    r"((?<!\$)\$(?!\$)[A-z0-9_\-\{]*)(\})",
                    str(input_parameters[param_name]),
                    working_string,
                )
                input_string = working_string
            else:
                raise SyntaxError(
                    "forgot opening { in parameter insertion: " + match[0] + "}"
                )
        for match in re.findall(
            r"((?<!\$)\$(?!\$)[A-z0-9_\-]*)(?![A-z0-9_\-])", input_string
        ):
            param_name = match.strip("$")
            if param_name in input_parameters.keys():
                working_string = re.sub(
                    r"((?<!\$)\$(?!\$)[A-z0-9_\-]*)(?![A-z0-9_\-])",
                    str(input_parameters[param_name]),
                    working_string,
                )
                input_string = working_string
            else:
                raise ValueError(
                    "Unknown parameter:"
                    + param_name
                    + ", please define it in the parameters section of the Workflow Definition."
                )
    return input_string
