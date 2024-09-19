"""Handles admin commands and related logic."""

from wei.types.interface_types import InterfaceMap
from wei.types.module_types import AdminCommands, Module, ModuleStatus
from wei.utils import threaded_task


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
