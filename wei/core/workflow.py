"""The module that initializes and runs the step by step WEI workflow"""

from typing import Any, Dict, List, Optional

from fastapi import UploadFile

from wei.core.data_classes import Step, Workcell, Workflow, WorkflowRun
from wei.core.module import validate_module_names
from wei.core.state_manager import StateManager
from wei.core.step import validate_step

state_manager = StateManager()


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
    wf_run.run_dir.mkdir(parents=True, exist_ok=True)
    wf_run.result_dir.mkdir(parents=True, exist_ok=True)

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
    if files:
        for file in files:
            print(file)
            file_path = wf_run.run_dir / file.filename
            with open(file_path, "wb") as f:
                f.write(file.file.read())
            for step in wf_run.steps:
                for step_file in step.files:
                    step.files[step_file] = str(file_path)
                    print(file_path)
    return wf_run
