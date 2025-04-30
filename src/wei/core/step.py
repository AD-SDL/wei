"""Functions related to WEI workflow steps."""

import traceback
from datetime import datetime
from typing import Tuple

from wei.core.events import send_event
from wei.core.location import free_source_and_target, update_source_and_target
from wei.core.loggers import Logger
from wei.core.module import clear_module_reservation, get_module_about
from wei.core.notifications import send_failed_step_notification
from wei.core.state_manager import state_manager
from wei.core.storage import get_workflow_run_directory
from wei.core.workflow_admin import wf_status_change
from wei.types import (
    Module,
    ModuleStatus,
    Step,
    StepResponse,
    StepStatus,
    WorkflowRun,
    WorkflowStatus,
)
from wei.types.datapoint_types import LocalFileDataPoint, ValueDataPoint
from wei.types.event_types import (
    WorkflowCompletedEvent,
    WorkflowFailedEvent,
    WorkflowStepEvent,
)
from wei.types.interface_types import InterfaceMap
from wei.utils import threaded_daemon


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
    return check_module_status(step, run_id) and check_dependency_status(step)


def check_module_status(step: Step, run_id: str):
    """Returns true if the module is able to run based on the module status"""
    module = state_manager.get_module(step.module)
    if module.state.status[ModuleStatus.READY] and not (
        module.state.status[ModuleStatus.LOCKED]
        or module.state.status[ModuleStatus.PAUSED]
        or module.state.status[ModuleStatus.CANCELLED]
    ):
        return True
    else:
        print(
            f"Can't run '{run_id}.{step.name}', module '{step.module}' is not idle. Module status: {module.state.status}"
        )
        return False


def check_dependency_status(step: Step):
    """Returns true if the module is able to run based on the step requirements"""
    return True


@threaded_daemon
def run_step(
    wf_run: WorkflowRun,
    module: Module,
) -> None:
    """Runs a single Step from a given workflow on a specified Module."""
    logger = Logger.get_workflow_run_logger(wf_run.run_id)
    step: Step = wf_run.steps[wf_run.step_index]
    while not wf_status_change.is_set():
        logger.debug(f"Started running step with name: {step.name}")
        logger.debug(step)
        interface = "simulate_callback" if wf_run.simulate else module.interface

        if (
            wf_run.status == WorkflowStatus.CANCELLED
        ):  # *** Not sure if boosts performance or not..
            return
        if wf_status_change.is_set():
            return

        try:
            step.start_time = datetime.now()
            status, data_key, error, files = InterfaceMap.interfaces[
                interface
            ].send_action(
                step=step,
                module=module,
                run_dir=get_workflow_run_directory(wf_run.run_id),
            )
            step_response = StepResponse(
                status=status,
                data=data_key,
                error=error,
                files=files,
            )
            if step_response.status == StepStatus.NOT_READY:
                print("STEP: not ready, ", wf_run.status, step_response.status)
                wf_run.status = WorkflowStatus.IN_PROGRESS
                step.result = step_response
                with state_manager.wc_state_lock():
                    wf_run.steps[wf_run.step_index] = step
                    state_manager.set_workflow_run(wf_run)
                    return
        except Exception as e:
            logger.debug(
                f"Exception occurred while running step with name: {step.name}"
            )
            logger.debug(str(e))
            logger.debug(traceback.format_exc())
            step_response = StepResponse(
                status=StepStatus.FAILED,
                error=str(e),
            )
            traceback.print_exc()
        else:
            logger.debug(f"Finished running step with name: {step.name}")

        step.end_time = datetime.now()
        step.duration = step.end_time - step.start_time

        labeled_data = None
        if step_response.data:
            labeled_data = {}
            for data_key in step_response.data:
                if step.data_labels is not None and data_key in step.data_labels:
                    label = step.data_labels[data_key]
                else:
                    label = data_key
                datapoint = ValueDataPoint(
                    label=label,
                    step_id=step.id,
                    workflow_id=wf_run.run_id,
                    experiment_id=wf_run.experiment_id,
                    value=step_response.data[data_key],
                )
                state_manager.set_datapoint(datapoint)
                labeled_data[label] = datapoint.id
        if step_response.files:
            if not labeled_data:
                labeled_data = {}
            for file_key in step_response.files:
                if step.data_labels is not None and file_key in step.data_labels:
                    label = step.data_labels[file_key]
                else:
                    label = file_key
                datapoint = LocalFileDataPoint(
                    step_id=step.id,
                    workflow_id=wf_run.run_id,
                    experiment_id=wf_run.experiment_id,
                    label=label,
                    path=str(step_response.files[file_key]),
                )
                state_manager.set_datapoint(datapoint)
                labeled_data[label] = datapoint.id

        send_event(WorkflowStepEvent.from_wf_run(wf_run=wf_run, step=step))
        step_response.data = labeled_data
        step.result = step_response
        if step_response.status == StepStatus.FAILED:
            logger.debug(f"Step {step.name} failed: {step_response.model_dump_json()}")
            wf_run.status = WorkflowStatus.FAILED
            wf_run.end_time = datetime.now()
            wf_run.duration = wf_run.end_time - wf_run.start_time
            send_event(
                WorkflowFailedEvent.from_wf_run(
                    wf_run=wf_run,
                )
            )
            send_failed_step_notification(wf_run, step)
        else:
            if wf_run.step_index + 1 == len(wf_run.steps):
                wf_run.status = WorkflowStatus.COMPLETED
                wf_run.end_time = datetime.now()
                wf_run.duration = wf_run.end_time - wf_run.start_time
                send_event(WorkflowCompletedEvent.from_wf_run(wf_run=wf_run))
            else:
                if wf_status_change.is_set():
                    return
                wf_run.status = WorkflowStatus.IN_PROGRESS
        with state_manager.wc_state_lock():
            if wf_status_change.is_set():
                return
            wf_run.steps[wf_run.step_index] = step
            update_source_and_target(wf_run)
            free_source_and_target(wf_run)
            clear_module_reservation(module)
            if wf_run.step_index < len(wf_run.steps) - 1:
                wf_run.step_index += 1
            state_manager.set_workflow_run(wf_run)
            return
    return
