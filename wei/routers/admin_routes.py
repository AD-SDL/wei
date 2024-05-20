"""Implements routes for the /admin commands"""

import os
import signal

from fastapi import APIRouter

from wei.config import Config
from wei.core.admin import (
    send_cancel,
    send_estop,
    send_pause,
    send_reset,
    send_resume,
    send_shutdown,
)
from wei.core.state_manager import StateManager
from wei.helpers import initialize_state

router = APIRouter()

state_manager = StateManager()


@router.api_route("/estop", methods=["POST"])
def estop_workcell() -> None:
    """E-stops a workcell"""
    for module in state_manager.get_all_modules().values():
        send_estop(module)
    state_manager.paused = True


@router.api_route("/estop/{module_name}", methods=["POST"])
def estop_module(module_name: str) -> None:
    """E-stops a module"""
    send_estop(state_manager.get_module(module_name))


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
    # TODO: workcell.cancel()


@router.api_route("/cancel/{module_name}", methods=["POST"])
def cancel_module(module_name: str) -> None:
    """Cancels a module"""
    send_cancel(state_manager.get_module(module_name))


@router.api_route("/shutdown", methods=["POST", "GET"])
def shutdown_workcell() -> None:
    """Shuts down the workcell"""
    for module in state_manager.get_all_modules().values():
        send_shutdown(module.shutdown)
    state_manager.shutdown = True
    os.kill(os.getpid(), signal.SIGTERM)


@router.api_route("/shutdown/{module_name}", methods=["POST"])
def shutdown_module(module_name: str) -> None:
    """Shuts down a module"""
    send_shutdown(state_manager.get_module(module_name))
