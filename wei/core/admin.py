"""Handles admin commands and related logic."""

from wei.core.data_classes import AdminCommands, Module
from wei.core.interface import InterfaceMap


def send_estop(module: Module) -> None:
    """E-stops a module"""
    if AdminCommands.ESTOP in module.about.admin_commands:
        InterfaceMap.interfaces[module.interface].send_admin_command(
            module, AdminCommands.ESTOP
        )
        print(f"Module {module.name} has been e-stopped.")
    else:
        print(f"Module {module.name} does not support e-stop.")
        send_safety_stop(module)


def send_safety_stop(module: Module) -> None:
    """Safety stops a module"""
    if AdminCommands.SAFETY_STOP in module.about.admin_commands:
        InterfaceMap.interfaces[module.interface].send_admin_command(
            module, AdminCommands.SAFETY_STOP
        )
        print(f"Module {module.name} has been safety stopped.")
    else:
        print(f"Module {module.name} does not support safety stop.")
        send_pause(module)
        send_lock(module)


def send_reset(module: Module) -> None:
    """Resets a module"""
    if AdminCommands.RESET in module.about.admin_commands:
        InterfaceMap.interfaces[module.interface].send_admin_command(
            module, AdminCommands.RESET
        )
        print(f"Module {module.name} has been reset.")
    else:
        print(f"Module {module.name} does not support resetting.")


def send_pause(module: Module) -> None:
    """Pauses a module"""
    if AdminCommands.PAUSE in module.about.admin_commands:
        InterfaceMap.interfaces[module.interface].send_admin_command(
            module, AdminCommands.PAUSE
        )
        print(f"Module {module.name} has been paused.")
    else:
        print(f"Module {module.name} does not support pausing.")
        send_cancel(module)


def send_resume(module: Module) -> None:
    """Resumes a module"""
    if AdminCommands.RESUME in module.about.admin_commands:
        InterfaceMap.interfaces[module.interface].send_admin_command(
            module, AdminCommands.RESUME
        )
        print(f"Module {module.name} has been resumed.")
    else:
        print(f"Module {module.name} does not support resuming.")


def send_cancel(module: Module) -> None:
    """Cancels a module"""
    if AdminCommands.CANCEL in module.about.admin_commands:
        InterfaceMap.interfaces[module.interface].send_admin_command(
            module, AdminCommands.CANCEL
        )
        print(f"Module {module.name} action has been canceled.")
    else:
        print(f"Module {module.name} does not support canceling.")


def send_lock(module: Module) -> None:
    """Locks a module, preventing it from being used until unlocked."""
    if AdminCommands.LOCK in module.about.admin_commands:
        InterfaceMap.interfaces[module.interface].send_admin_command(
            module, AdminCommands.LOCK
        )
        print(f"Module {module.name} has been locked.")
    else:
        print(f"Module {module.name} does not support locking.")


def send_unlock(module: Module) -> None:
    """Unlocks a module, allowing it to be used."""
    if AdminCommands.UNLOCK in module.about.admin_commands:
        InterfaceMap.interfaces[module.interface].send_admin_command(
            module, AdminCommands.UNLOCK
        )
        print(f"Module {module.name} has been unlocked.")
    else:
        print(f"Module {module.name} does not support unlocking.")


def send_shutdown(module: Module) -> None:
    """Shuts down a module"""
    if AdminCommands.SHUTDOWN in module.about.admin_commands:
        InterfaceMap.interfaces[module.interface].send_admin_command(
            module, AdminCommands.SHUTDOWN
        )
        print(f"Module {module.name} has been shut down.")
    else:
        print(f"Module {module.name} does not support shutting down.")
