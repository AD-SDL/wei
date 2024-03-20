"""Provides methods and classes to work with modules"""

import concurrent.futures
import traceback
from typing import Union

from wei.core.data_classes import (
    Module,
    ModuleAbout,
    ModuleStatus,
    Workcell,
    Workflow,
    WorkflowStatus,
)
from wei.core.interface import InterfaceMap
from wei.core.state_manager import StateManager
from wei.core.workcell import find_step_module

state_manager = StateManager()


def initialize_workcell_modules() -> None:
    """Initialize all active modules in the workcell."""
    for module in state_manager.get_workcell().modules:
        if not module.active:
            continue
        state_manager.set_module(module.name, module)


def update_active_modules() -> None:
    """Update all active modules in the workcell."""
    with concurrent.futures.ThreadPoolExecutor() as executor:
        module_futures = []
        for module_name, module in state_manager.get_all_modules().items():
            if module.active:
                module_future = executor.submit(update_module, module_name, module)
                module_futures.append(module_future)

        # Wait for all module updates to complete
        concurrent.futures.wait(module_futures)


def update_module(module_name: str, module: Module) -> None:
    """Update a single module's state and about information."""
    try:
        state = query_module_status(module)
        if state != module.state:
            if module.state in [ModuleStatus.INIT, ModuleStatus.UNKNOWN]:
                module.about = get_module_about(module, require_schema_compliance=False)
            module.state = state
            with state_manager.state_lock():
                state_manager.set_module(module_name, module)
        if module.reserved:
            reserving_wf = state_manager.get_workflow_run(module.reserved)
            if (
                reserving_wf.status
                in [
                    WorkflowStatus.COMPLETED,
                    WorkflowStatus.FAILED,
                ]
                or reserving_wf.steps[reserving_wf.step_index].module != module.name
            ):
                # *The module is reserved by a workflow,
                # *but that workflow isn't actually using the module,
                # *so release the reservation, and allow the current workflow to proceed
                print(f"Clearing reservation on module {module_name}")
                with state_manager.state_lock():
                    clear_module_reservation(module)
    except Exception:
        traceback.print_exc()
        print(f"Unable to update module {module_name}")


def query_module_status(module: Module) -> ModuleStatus:
    """Update a single module's state by querying the module."""
    module_name = module.name
    state = ModuleStatus.UNKNOWN
    if module.interface in InterfaceMap.interfaces:
        try:
            interface = InterfaceMap.interfaces[module.interface]
            working_state = interface.get_state(module)
            if isinstance(working_state, dict):
                working_state = working_state["State"]

            if not (working_state == "" or working_state == "UNKNOWN"):
                if module.state in [ModuleStatus.INIT, ModuleStatus.UNKNOWN]:
                    print("Module Found: " + str(module_name))
                state = ModuleStatus(working_state)
        except Exception as e:
            if module.state == ModuleStatus.INIT:
                print(e)
                print("Can't Find Module: " + str(module_name))
    else:
        if module.state == ModuleStatus.INIT:
            print("No Module Interface for Module", str(module_name))
    return state


def validate_module_names(workflow: Workflow, workcell: Workcell) -> None:
    """
    Validates that
        - the modules in the workflow.flowdef are also in the workflow.modules
        - the modules in the workflow.modules are also in the workcell.modules
        - by extension, the modules in workflow.flowdef are also in the workcell.modules
    """
    # Validate that each step's module is also in the Workflow at the top
    for step in workflow.flowdef:
        if not any([step.module == module_name for module_name in workflow.modules]):
            raise ValueError(f"Module {step.module} not in flow modules")

    # Validate that all the modules listed in the workflow are also in the workcell
    [find_step_module(workcell, module_name) for module_name in workflow.modules]


def get_module_about(
    module: Module, require_schema_compliance: bool = True
) -> Union[ModuleAbout, None]:
    """Gets a module's about information"""
    module_name = module.name
    if module.interface in InterfaceMap.interfaces:
        try:
            interface = InterfaceMap.interfaces[module.interface]
            response = interface.get_about(module)
            try:
                about = ModuleAbout(**interface.get_about(module))
            except Exception:
                if require_schema_compliance:
                    return None
                about = response
            return about
        except Exception as e:
            print(e)
            print("Unable to get about information for Module " + str(module_name))
    else:
        print("Module Interface not supported for Module ", str(module_name))
    return None


def update_module_reservation(module: Module, run_id: Union[str, None]) -> Module:
    """Updates a module's reservation"""
    module.reserved = run_id
    return module


def reserve_module(module: Module, run_id: str) -> None:
    """Reserves a module for a given run"""
    state_manager.update_module(module.name, update_module_reservation, run_id)


def clear_module_reservation(module: Module):
    """Clears a module's reservation"""
    state_manager.update_module(module.name, update_module_reservation, None)
