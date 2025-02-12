"""Implements routes for the /admin commands"""

import os
import signal
import time
from fastapi import APIRouter, HTTPException

from wei.config import Config
from wei.core.admin import (
    send_cancel,
    send_cancel_wf,
    send_lock,
    send_pause,
    send_pause_wf,
    send_reset,
    send_resume,
    send_safety_stop,
    send_shutdown,
    send_unlock,
    check_can_send_admin_command
)
from wei.core.state_manager import state_manager
from wei.core.workflow import cancel_active_workflow_runs, cancel_workflow_run
from wei.utils import initialize_state
from wei.routers.workflow_routes import get_run
from wei.core.module import clear_module_reservation
from wei.types.module_types import ModuleStatus, AdminCommands

router = APIRouter()


@router.api_route("/safety_stop", methods=["POST"])
def safety_stop_workcell() -> None:
    """Safety-stops a workcell"""
    for module in state_manager.get_all_modules().values():
        send_safety_stop(module)
    cancel_active_workflow_runs()
    state_manager.paused = True


@router.api_route("/safety_stop/{module_name}", methods=["POST"])
def safety_stop_module(module_name: str) -> None:
    """Safety-stops a module"""
    send_safety_stop(state_manager.get_module(module_name))


@router.api_route("/reset", methods=["POST"])
def reset_workcell() -> None:
    """Resets the entire workcell"""
    for module in state_manager.get_all_modules().values():
        send_reset(module)
    workcell = state_manager.get_workcell()
    state_manager.clear_state(
        reset_locations=Config.reset_locations,
        clear_workflow_runs=Config.clear_workflow_runs,
    )
    initialize_state(workcell=workcell)


@router.api_route("/reset/{module_name}", methods=["POST"])
def reset_module(module_name: str) -> None:
    """Resets a module"""
    send_reset(state_manager.get_module(module_name))


@router.api_route("/pause", methods=["POST"])
def pause_workcell() -> None:
    """Pauses the workcell"""
    for module in state_manager.get_all_modules().values():
        send_pause(module)
    state_manager.paused = True


@router.api_route("/pause/{module_name}", methods=["POST"])
def pause_module(module_name: str) -> None:
    """Pauses a module"""
    send_pause(state_manager.get_module(module_name))

@router.api_route("/pause_wf/{wf_run_id}", methods=["POST"])
def pause_workflow(wf_run_id: str) -> None:
    """Pauses a workflow"""
    for module in state_manager.get_all_modules().values():
        send_pause(module)
        clear_module_reservation(module)
    # state_manager.paused = True
    test = send_pause_wf(get_run(wf_run_id))
    while test != True:
        time.sleep(5)
    for module in state_manager.get_all_modules().values():
        send_resume(module)
    # state_manager.paused = False

@router.api_route("/resume", methods=["POST"])
def resume_workcell() -> None:
    """Resumes the workcell"""
    for module in state_manager.get_all_modules().values():
        send_resume(module)
    state_manager.paused = False


@router.api_route("/resume/{module_name}", methods=["POST"])
def resume_module(module_name: str) -> None:
    """Resumes a module"""
    send_resume(state_manager.get_module(module_name))


@router.api_route("/cancel", methods=["POST"])
def cancel_workcell() -> None:
    """Cancels the workcell"""
    for module in state_manager.get_all_modules().values():
        send_cancel(module)
    cancel_active_workflow_runs()


@router.api_route("/cancel/{module_name}", methods=["POST"])
def cancel_module(module_name: str) -> None:
    """Cancels a module"""
    send_cancel(state_manager.get_module(module_name))

@router.api_route("/cancel_wf/{wf_run_id}", methods=["POST"])
def cancel_workflow(wf_run_id: str) -> None:
    """Cancels a workflow"""
    ## vers 1.
    # # for module in state_manager.get_all_modules().values():
    # #     send_cancel(module)
    # pause_workcell()
    # cancelled = send_cancel_wf(get_run(wf_run_id))  # Not sure if this does anything..,
    # while not cancelled:
    #     time.sleep(5)
    # resume_workcell()
    # # for module in state_manager.get_all_modules().values():
    # #     send_reset(module)

    ## vers 2.
    #pause_workcell()
    state_manager.paused = True
    send_cancel_wf(get_run(wf_run_id))
    state_manager.paused = False
    #resume_workcell()

    ## vers 3.
    # cancel_workflow_run(get_run(wf_run_id))

@router.api_route("/shutdown", methods=["POST"])
def shutdown_workcell(modules: bool = False) -> None:
    """Shuts down the workcell"""
    if modules:
        for module in state_manager.get_all_modules().values():
            send_shutdown(module)
    state_manager.shutdown = True
    os.kill(os.getpid(), signal.SIGTERM)


@router.api_route("/shutdown/{module_name}", methods=["POST"])
def shutdown_module(module_name: str) -> None:
    """Shuts down a module"""
    send_shutdown(state_manager.get_module(module_name))


@router.api_route("/lock", methods=["POST"])
def lock_workcell() -> None:
    """Locks the workcell"""
    for module in state_manager.get_all_modules().values():
        send_lock(module)
    state_manager.locked = True


@router.api_route("/lock/{module_name}", methods=["POST"])
def lock_module(module_name: str) -> None:
    """Locks a module"""
    send_lock(state_manager.get_module(module_name))


@router.api_route("/unlock", methods=["POST"])
def unlock_workcell() -> None:
    """Unlocks the workcell"""
    for module in state_manager.get_all_modules().values():
        send_unlock(module)
    state_manager.locked = False


@router.api_route("/unlock/{module_name}", methods=["POST"])
def unlock_module(module_name: str) -> None:
    """Unlocks a module"""
    send_unlock(state_manager.get_module(module_name))
