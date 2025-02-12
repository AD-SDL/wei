"""Handles admin commands and related logic."""

from wei.types.interface_types import InterfaceMap
from wei.types.module_types import AdminCommands, Module, ModuleStatus
from wei.types.workflow_types import WorkflowRun, WorkflowStatus
from wei.core.workflow import cancel_workflow_run, pause_workflow_run
from wei.core.state_manager import state_manager
from wei.core.module import clear_module_reservation
from wei.types.event_types import WorkflowCancelled
from wei.core.events import send_event
from wei.utils import threaded_task
import time
import datetime


@threaded_task
def send_safety_stop(module: Module) -> None:
    """Safety stops a module"""
    if check_can_send_admin_command(module, AdminCommands.SAFETY_STOP):
        InterfaceMap.interfaces[module.interface].send_admin_command(
            module, AdminCommands.SAFETY_STOP
        )
        print(f"Module {module.name} has been safety-stopped.")
    else:
        print(f"Module {module.name} does not support safety stop.")
        send_pause(module)


@threaded_task
def send_reset(module: Module) -> None:
    """Resets a module"""
    if check_can_send_admin_command(module, AdminCommands.RESET):
        InterfaceMap.interfaces[module.interface].send_admin_command(
            module, AdminCommands.RESET
        )
        print(f"Module {module.name} has been reset.")
    else:
        print(f"Module {module.name} does not support resetting.")


@threaded_task
def send_pause(module: Module) -> None:
    """Pauses a module"""
    if check_can_send_admin_command(module, AdminCommands.PAUSE):
        InterfaceMap.interfaces[module.interface].send_admin_command(
            module, AdminCommands.PAUSE
        )
        print(f"Module {module.name} has been paused.")
    else:
        print(f"Module {module.name} does not support pausing.")
        send_cancel(module)

def send_pause_wf(workflow: WorkflowRun):
    """Pauses a workflow"""
    if check_can_send_admin_command_wf(workflow, AdminCommands.PAUSE):
        while not workflow.status == WorkflowStatus.PAUSED:
            pause_workflow_run(workflow)
        time.sleep(3)
        for wf_run in state_manager.get_all_workflow_runs().values():
            if (wf_run.status in [WorkflowStatus.IN_PROGRESS]): # & (workflow.run_id == wf_run.run_id):   
                pause_workflow_run(wf_run)
                time.sleep(1)
                return True
        return True
    else:
        print(f"Error pausing workflow {workflow.label}")


@threaded_task
def send_resume(module: Module) -> None:
    """Resumes a module"""
    if check_can_send_admin_command(module, AdminCommands.RESUME):
        InterfaceMap.interfaces[module.interface].send_admin_command(
            module, AdminCommands.RESUME
        )
        print(f"Module {module.name} has been resumed.")
    else:
        print(f"Module {module.name} does not support resuming.")


@threaded_task
def send_cancel(module: Module) -> None:
    """Cancels a module"""
    if check_can_send_admin_command(module, AdminCommands.CANCEL):
        InterfaceMap.interfaces[module.interface].send_admin_command(
            module, AdminCommands.CANCEL
        )
        print(f"Module {module.name} action has been canceled.")
    else:
        print(f"Module {module.name} does not support canceling.")

@threaded_task # ** try with and wo thread
def send_cancel_wf(workflow: WorkflowRun):
    """Cancels a workflow"""
    if check_can_send_admin_command_wf(workflow, AdminCommands.CANCEL):
        cancel_workflow_run(workflow)
        ## vers 1.
        # while not workflow.status == WorkflowStatus.CANCELLED:
        #     cancel_workflow_run(workflow)
        # time.sleep(3)
        # for wf_run in state_manager.get_all_workflow_runs().values():
        #     if wf_run.status in [WorkflowStatus.IN_PROGRESS]:
        #         cancel_workflow_run(wf_run)
        #         time.sleep(1)
        #         return True
        # print(f"Workflow {workflow.label} has been canceled.")
        # return True

        ## vers 2.
        # workflow.status = WorkflowStatus.CANCELLED
        # with state_manager.wc_state_lock():

        #     workflow.status = WorkflowStatus.CANCELLED
        #     workflow.end_time = datetime.now()
        #     workflow.duration = workflow.end_time - workflow.start_time

        #     for step in workflow.steps:
        #         module = state_manager.get_module(step.module)
        #         clear_module_reservation(module)

        #     state_manager.set_workflow_run(workflow)

        #     send_event(WorkflowCancelled.from_wf_run(workflow=workflow))
        #     print(f"Workflow run with id {workflow.run_id} has been cancelled.")

    else:
        print(f"Error cancelling workflow {workflow.label}")

@threaded_task
def send_shutdown(module: Module) -> None:
    """Shuts down a module"""
    if check_can_send_admin_command(module, AdminCommands.SHUTDOWN):
        InterfaceMap.interfaces[module.interface].send_admin_command(
            module, AdminCommands.SHUTDOWN
        )
        print(f"Module {module.name} has been shut down.")
    else:
        print(f"Module {module.name} does not support shutting down.")


@threaded_task
def send_lock(module: Module) -> None:
    """Locks a module"""
    if check_can_send_admin_command(module, AdminCommands.LOCK):
        InterfaceMap.interfaces[module.interface].send_admin_command(
            module, AdminCommands.LOCK
        )
        print(f"Module {module.name} has been locked.")
    else:
        print(f"Module {module.name} does not support locking.")


@threaded_task
def send_unlock(module: Module) -> None:
    """Unlocks a module"""
    if check_can_send_admin_command(module, AdminCommands.UNLOCK):
        InterfaceMap.interfaces[module.interface].send_admin_command(
            module, AdminCommands.UNLOCK
        )
        print(f"Module {module.name} has been unlocked.")
    else:
        print(f"Module {module.name} does not support unlocking.")


def check_can_send_admin_command(module: Module, command: AdminCommands) -> bool:
    """Checks if a module can send an admin command"""
    return not module.state.status == ModuleStatus.UNKNOWN and (
        module.about is None or command in module.about.admin_commands
    )

def check_can_send_admin_command_wf(workflow: WorkflowRun, command: AdminCommands) -> bool: # ***
    """Checks if an admin command can be sent to workflow"""
    return not workflow.status == WorkflowStatus.UNKNOWN
