"""Provides methods and classes to work with modules"""

import concurrent.futures
import json
import traceback
import warnings
from typing import Union

from wei.core.state_manager import state_manager
from wei.core.workcell import find_step_module
from wei.types import Module, ModuleAbout, Workcell, Workflow, WorkflowStatus
from wei.types.interface_types import InterfaceMap
from wei.types.module_types import LegacyModuleState, ModuleState, ModuleStatus


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
        old_state = module.state
        old_about = module.about
        if module.interface in InterfaceMap.interfaces:
            try:
                interface = InterfaceMap.interfaces[module.interface]
                working_state = interface.get_state(module)
                if isinstance(working_state, str):
                    working_state = json.loads(working_state)
                try:
                    module.state = ModuleState.model_validate(working_state)
                except Exception:
                    # traceback.print_exc()
                    module.state = LegacyModuleState.model_validate(
                        working_state
                    ).to_modern()
                    warnings.warn(
                        message=f"Module {module.name} is using the Legacy State Schema.",
                        category=UserWarning,
                        stacklevel=1,
                    )
            except Exception as e:
                warnings.warn(
                    message=f"Error getting state for module {module.name}.",
                    category=UserWarning,
                    stacklevel=1,
                )
                module.state = ModuleState(
                    status=ModuleStatus.UNKNOWN, error=f"Error getting state: {e}"
                )
        if module.state.status != ModuleStatus.UNKNOWN and module.about is None:
            module.about = get_module_about(module)
        if old_state != module.state or old_about != module.about:
            with state_manager.wc_state_lock():
                state_manager.set_module(module_name, module)
        if module.reserved:
            reserving_wf = state_manager.get_workflow_run(module.reserved)
            if (
                reserving_wf.status
                in [
                    WorkflowStatus.COMPLETED,
                    WorkflowStatus.FAILED,
                    WorkflowStatus.CANCELLED,
                    WorkflowStatus.UNKNOWN,
                ]
                or reserving_wf.steps[reserving_wf.step_index].module != module.name
            ):
                # *The module is reserved by a workflow,
                # *but that workflow isn't actually using the module,
                # *so release the reservation, and allow the current workflow to proceed
                print(f"Clearing reservation on module {module_name}")
                with state_manager.wc_state_lock():
                    clear_module_reservation(module)
    except Exception:
        traceback.print_exc()
        warnings.warn(
            message=f"Unable to update module {module_name}",
            category=UserWarning,
            stacklevel=1,
        )


def validate_module_names(workflow: Workflow, workcell: Workcell) -> None:
    """
    Validates that the modules in the workflow.flowdef are in the workcell.modules
    """
    [
        find_step_module(workcell, module_name)
        for module_name in [step.module for step in workflow.flowdef]
    ]


def get_module_about(module: Module) -> Union[ModuleAbout, None]:
    """Gets a module's about information"""
    module_name = module.name
    if module.interface in InterfaceMap.interfaces:
        try:
            interface = InterfaceMap.interfaces[module.interface]
            try:
                about = ModuleAbout(**interface.get_about(module))
            except Exception:
                warnings.warn(
                    message=f"Unable to parse about information for Module {module_name}",
                    category=UserWarning,
                    stacklevel=1,
                )
                about = None
            return about
        except Exception:
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
