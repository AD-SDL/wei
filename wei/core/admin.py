"""Handles admin commands and related logic."""

from wei.core.data_classes import AdminCommands, Module
from wei.core.interface import InterfaceMap


def estop_module(module: Module) -> None:
    """E-stops a module"""
    if AdminCommands.ESTOP in module.about.admin_commands:
        InterfaceMap.interfaces[module.interface].send_admin_command(
            module, AdminCommands.ESTOP
        )
        print(f"Module {module.name} has been e-stopped.")
    else:
        print(f"Module {module.name} does not support e-stop.")
        safety_stop_module(module)


def safety_stop_module(module: Module) -> None:
    """E-stops a module"""
    if AdminCommands.SAFETY_STOP in module.about.admin_commands:
        InterfaceMap.interfaces[module.interface].send_admin_command(
            module, AdminCommands.SAFETY_STOP
        )
        print(f"Module {module.name} has been safety stopped.")
    else:
        print(f"Module {module.name} does not support safety stop.")
        pause_module(module)


def reset_module(module: Module) -> None:
    """Resets a module"""
    InterfaceMap.interfaces[module.interface].send_admin_command(
        module, AdminCommands.RESET
    )
    print(f"Module {module.name} has been reset.")


def pause_module(module: Module) -> None:
    """Pauses a module"""
    if AdminCommands.PAUSE in module.about.admin_commands:
        InterfaceMap.interfaces[module.interface].send_admin_command(
            module, AdminCommands.PAUSE
        )
        print(f"Module {module.name} has been paused.")
    else:
        print(f"Module {module.name} does not support pausing.")
        cancel_module(module)


def cancel_module(module: Module) -> None:
    """Cancels a module"""
    if AdminCommands.CANCEL in module.about.admin_commands:
        InterfaceMap.interfaces[module.interface].send_admin_command(
            module, AdminCommands.CANCEL
        )
        print(f"Module {module.name} action has been canceled.")
    else:
        print(f"Module {module.name} does not support canceling.")
