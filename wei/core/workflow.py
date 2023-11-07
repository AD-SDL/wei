"""The module that initializes and runs the step by step WEI workflow"""
from typing import Any, Dict, Optional

from wei.core.data_classes import (
    Module,
    Step,
    StepResponse,
    StepStatus,
    WorkcellData,
    Workflow,
    WorkflowRun,
    WorkflowStatus,
)
from wei.core.experiment import Experiment, get_experiment_event_server
from wei.core.interface import InterfaceMap
from wei.core.location import update_source_and_target
from wei.core.loggers import WEI_Logger
from wei.core.module import validate_module_names
from wei.core.state_manager import StateManager

state_manager = StateManager()


def check_step(experiment_id: str, run_id: str, step: Step) -> bool:
    """Check if a step is valid."""
    if "target" in step.locations:
        location = state_manager.get_location(step.locations["target"])
        if not (location.state == "Empty") or not (
            (len(location.queue) > 0 and location.queue[0] == str(run_id))
        ):
            return False

    if "source" in step.locations:
        location = state_manager.get_location(step.locations["source"])
        if not (location.state == str(experiment_id)):
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
) -> None:
    """Runs a single Step from a given workflow on a specified Module."""
    logger = WEI_Logger.get_workflow_run_logger(wf_run)
    step: Step = wf_run.steps[wf_run.step_index]

    logger.info(f"Started running step with name: {step.name}")
    logger.debug(step)

    interface = "simulate_callback" if wf_run.simulate else module.interface

    experiment = Experiment(experiment_id=wf_run.experiment_id)

    try:
        action_response, action_msg, action_log = InterfaceMap.interfaces[
            interface
        ].send_action(
            step=step, module=module, experiment_path=experiment.experiment_dir
        )
        step_response = StepResponse(
            action_response=action_response,
            action_msg=action_msg,
            action_log=action_log,
        )
    except Exception as e:
        logger.info(f"Exception occurred while running step with name: {step.name}")
        logger.debug(str(e))
        step_response = StepResponse(
            action_response=StepStatus.FAILED,
            action_msg="Exception occurred while running step",
            action_log=str(e),
        )
    else:
        logger.info(f"Finished running step with name: {step.name}")

    wf_run.hist[step.name] = step_response
    wf_run.hist["run_dir"] = str(wf_run.run_dir)
    if step_response.action_response == StepStatus.FAILED:
        wf_run.status = WorkflowStatus.FAILED
        get_experiment_event_server(wf_run.experiment_id).log_wf_failed(
            wf_run.name, wf_run.run_id
        )
    else:
        if wf_run.step_index + 1 == len(wf_run.steps):
            wf_run.status = WorkflowStatus.COMPLETED
            get_experiment_event_server(wf_run.experiment_id).log_wf_end(
                wf_run.name, wf_run.run_id
            )
        else:
            wf_run.status = WorkflowStatus.QUEUED
        wf_run.step_index += 1
    with state_manager.state_lock():
        update_source_and_target(wf_run)
        state_manager.set_workflow_run(wf_run)


def create_run(
    workflow: Workflow,
    workcell: WorkcellData,
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
    print(workflow)
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
        replace_positions(workcell, step)
        if payload:
            inject_payload(payload, step)
        steps.append(step)

    wf_run.steps = steps

    return wf_run


def replace_positions(workcell: WorkcellData, step: Step) -> None:
    """Replaces the positions in the step with the actual positions from the workcell"""
    if isinstance(step.args, dict) and len(step.args) > 0 and workcell.locations:
        if step.module in workcell.locations.keys():
            for key, value in step.args.items():
                # if hasattr(value, "__contains__") and "positions" in value:
                if str(value) in workcell.locations[step.module].keys():
                    step.args[key] = workcell.locations[step.module][value]


def inject_payload(payload: Dict[str, Any], step: Step) -> None:
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
