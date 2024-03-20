"""Implements routes for the /admin commands"""

import os
import signal

from fastapi import APIRouter

from wei.core.admin import (
    send_cancel,
    send_estop,
    send_pause,
    send_reset,
    send_resume,
    send_shutdown,
)
from wei.core.state_manager import StateManager

router = APIRouter()

state_manager = StateManager()


@router.api_route("/estop", methods=["POST", "GET"])
def estop_workcell() -> None:
    """E-stops a workcell"""
    for module in state_manager.get_all_modules().values():
        send_estop(module)


@router.api_route("/estop/{module_name}", methods=["POST", "GET"])
def estop_module(module_name: str) -> None:
    """E-stops a module"""
    send_estop(state_manager.get_module(module_name))


@router.api_route("/reset", methods=["POST", "GET"])
def reset_workcell() -> None:
    """Resets the entire workcell"""
    for module in state_manager.get_all_modules().values():
        send_reset(module)
    # TODO: workcell.reset()


@router.api_route("/reset/{module_name}", methods=["POST", "GET"])
def reset_module(module_name: str) -> None:
    """Resets a module"""
    send_reset(state_manager.get_module(module_name))


@router.api_route("/pause", methods=["POST", "GET"])
def pause_workcell() -> None:
    """Pauses the workcell"""
    for module in state_manager.get_all_modules().values():
        send_pause(module)
    # TODO: workcell.pause()


@router.api_route("/pause/{module_name}", methods=["POST", "GET"])
def pause_module(module_name: str) -> None:
    """Pauses a module"""
    send_pause(state_manager.get_module(module_name))


@router.api_route("/resume", methods=["POST", "GET"])
def resume_workcell() -> None:
    """Resumes the workcell"""
    for module in state_manager.get_all_modules().values():
        send_resume(module)
    # TODO: workcell.resume()


@router.api_route("/resume/{module_name}", methods=["POST", "GET"])
def resume_module(module_name: str) -> None:
    """Resumes a module"""
    send_resume(state_manager.get_module(module_name))


@router.api_route("/cancel", methods=["POST", "GET"])
def cancel_workcell() -> None:
    """Cancels the workcell"""
    for module in state_manager.get_all_modules().values():
        send_cancel(module)
    # TODO: workcell.cancel()


@router.api_route("/cancel/{module_name}", methods=["POST", "GET"])
def cancel_module(module_name: str) -> None:
    """Cancels a module"""
    send_cancel(state_manager.get_module(module_name))


@router.api_route("/shutdown", methods=["POST", "GET"])
def shutdown_workcell() -> None:
    """Shuts down the workcell"""
    for module in state_manager.get_all_modules().values():
        send_shutdown(module.shutdown)
    # TODO: state_manager.shutdown() to halt engine
    os.kill(os.getpid(), signal.SIGINT)


@router.api_route("/shutdown/{module_name}", methods=["POST", "GET"])
def shutdown_module(module_name: str) -> None:
    """Shuts down a module"""
    send_shutdown(state_manager.get_module(module_name))
