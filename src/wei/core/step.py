"""Functions related to WEI workflow steps."""

import traceback
from datetime import datetime
from typing import Tuple

from wei.config import Config
from wei.core.events import send_event
from wei.core.location import free_source_and_target, update_source_and_target
from wei.core.loggers import Logger
from wei.core.module import clear_module_reservation, get_module_about
from wei.core.notifications import send_failed_step_notification
from wei.core.state_manager import StateManager
from wei.core.storage import get_workflow_run_directory
from wei.types import (
    Module,
    ModuleStatus,
    Step,
    StepResponse,
    StepStatus,
    WorkflowRun,
    WorkflowStatus,
)
from wei.types.event_types import (
    WorkflowCompletedEvent,
    WorkflowFailedEvent,
    WorkflowStepEvent,
)
from wei.types.interface_types import InterfaceMap

state_manager = StateManager()


def validate_step(step: Step) -> Tuple[bool, str]:
    """Check if a step is valid based on the module's about"""
    if step.module in [module.name for module in state_manager.get_workcell().modules]:
        module = state_manager.get_module(step.module)
        about = get_module_about(module)
        if about is None:
            return (
                True,
                f"Module {step.module} didn't return proper about information, skipping validation",
            )
        for action in about.actions:
            if step.action == action.name:
                for action_arg in action.args:
                    if action_arg.name not in step.args and action_arg.required:
                        return (
                            False,
                            f"Step '{step.name}': Module {step.module}'s action, '{step.action}', is missing arg '{action_arg.name}'",
                        )
                    # TODO: Action arg type validation goes here
                for action_file in action.files:
                    if action_file.name not in step.files and action_file.required:
                        return (
                            False,
                            f"Step '{step.name}': Module {step.module}'s action, '{step.action}', is missing file '{action_file.name}'",
                        )
                return True, f"Step '{step.name}': Validated successfully"

        return (
            False,
            f"Step '{step.name}': Module {step.module} has no action '{step.action}'",
        )
    else:
        return (
            False,
            f"Step '{step.name}': Module {step.module} is not defined in workcell",
        )


def check_step(experiment_id: str, run_id: str, step: Step) -> bool:
    """Check if a step is able to be run by the workcell."""
    if Config.verify_locations_before_transfer:
        if "target" in step.locations:
            location = state_manager.get_location(step.locations["target"])
            if not (location.state == "Empty"):
                print(f"Can't run {run_id}.{step.name}, target is not empty")
                return False
            if location.reserved and location.reserved != run_id:
                print(f"Can't run {run_id}.{step.name}, target is reserved")
                return False
        if "source" in step.locations:
            location = state_manager.get_location(step.locations["source"])
            if not (location.state == str(experiment_id)):
                print(
                    f"Can't run {run_id}.{step.name}, source asset doesn't belong to experiment"
                )
                return False
            if location.reserved and location.reserved != run_id:
                print(f"Can't run {run_id}.{step.name}, source is reserved")
                return False
    module = state_manager.get_module(step.module)
    if module.state.status != ModuleStatus.IDLE:
        print(f"Can't run {run_id}.{step.name}, module is not idle")
        return False
    if module.reserved and module.reserved != run_id:
        print(f"Can't run {run_id}.{step.name}, module is reserved")
        return False
    return True


def run_step(
    wf_run: WorkflowRun,
    module: Module,
) -> None:
    """Runs a single Step from a given workflow on a specified Module."""
    logger = Logger.get_workflow_run_logger(wf_run.run_id)
    step: Step = wf_run.steps[wf_run.step_index]

    logger.debug(f"Started running step with name: {step.name}")
    logger.debug(step)

    interface = "simulate_callback" if wf_run.simulate else module.interface

    try:
        step.start_time = datetime.now()
        action_response, action_msg, action_log = InterfaceMap.interfaces[
            interface
        ].send_action(
            step=step, module=module, run_dir=get_workflow_run_directory(wf_run.run_id)
        )
        step_response = StepResponse(
            action_response=action_response,
            action_msg=action_msg,
            action_log=action_log,
        )
    except Exception as e:
        logger.debug(f"Exception occurred while running step with name: {step.name}")
        logger.debug(str(e))
        logger.debug(traceback.format_exc())
        step_response = StepResponse(
            action_response=StepStatus.FAILED,
            action_msg="Exception occurred while running step",
            action_log=str(e),
        )
        traceback.print_exc()
    else:
        logger.debug(f"Finished running step with name: {step.name}")

    step.end_time = datetime.now()
    step.duration = step.end_time - step.start_time
    step.result = step_response
    if step.result.action_response == StepStatus.FAILED:
        send_failed_step_notification(wf_run, step)
    send_event(WorkflowStepEvent.from_wf_run(wf_run=wf_run, step=step))
    wf_run.hist[step.name] = step_response
    if step_response.action_response == StepStatus.FAILED:
        logger.debug(f"Step {step.name} failed: {step_response.model_dump_json()}")
        wf_run.status = WorkflowStatus.FAILED
        wf_run.end_time = datetime.now()
        wf_run.duration = wf_run.end_time - wf_run.start_time
        send_event(
            WorkflowFailedEvent.from_wf_run(
                wf_run=wf_run,
            )
        )
    else:
        if wf_run.step_index + 1 == len(wf_run.steps):
            wf_run.status = WorkflowStatus.COMPLETED
            wf_run.end_time = datetime.now()
            wf_run.duration = wf_run.end_time - wf_run.start_time
            send_event(WorkflowCompletedEvent.from_wf_run(wf_run=wf_run))
        else:
            wf_run.status = WorkflowStatus.IN_PROGRESS
    with state_manager.wc_state_lock():
        wf_run.steps[wf_run.step_index] = step
        update_source_and_target(wf_run)
        free_source_and_target(wf_run)
        clear_module_reservation(module)
        if wf_run.step_index < len(wf_run.steps) - 1:
            wf_run.step_index += 1
        state_manager.set_workflow_run(wf_run)
