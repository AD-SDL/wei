"""Provides methods and classes to work with modules"""


from wei.config import Config
from wei.core.data_classes import Module, ModuleStatus, WorkcellData, Workflow
from wei.core.interface import InterfaceMap
from wei.core.state_manager import StateManager
from wei.core.workcell import find_step_module

state_manager = StateManager(Config.workcell_file, Config.redis_host, Config.redis_port)


def initialize_workcell_modules():
    for module in state_manager.get_workcell().modules:
        if not module.active:
            continue
        state_manager.set_module(module.name, module)


def update_active_modules(initial: bool = False):
    with state_manager.state_lock():
        for module_name, module in state_manager.get_all_modules().items():
            if module.active:
                state = query_module_status(module)
                if state != module.state:
                    module.state = state
                    state_manager.set_module(module_name, module)


def query_module_status(module: Module) -> ModuleStatus:
    """Update a single module's state by querying the module."""
    module_name = module.name
    if module.interface in InterfaceMap.interfaces:
        try:
            interface = InterfaceMap.interfaces[module.interface]
            state = interface.get_state(module.config)
            if isinstance(state, dict):
                state = state["State"]

            if not (state == ""):
                if module.state == ModuleStatus.INIT:
                    print("Module Found: " + str(module_name))
                return ModuleStatus(state)
            else:
                module.state = ModuleStatus.UNKNOWN
        except Exception as e:  # noqa
            if module.state == ModuleStatus.INIT:
                print(e)
                print("Can't Find Module: " + str(module_name))
    else:
        if module.state == ModuleStatus.INIT:
            print("No Module Interface for Module", str(module_name))
            return ModuleStatus.UNKNOWN


def validate_module_names(workflow: Workflow, workcell: WorkcellData):
    """
    Validates that
        - the modules in the workflow.flowdef are also in the workflow.modules
        - the modules in the workflow.modules are also in the workcell.modules
        - by extension, the modules in workflow.flowdef are also in the workcell.modules
    """
    # Validate that each step's module is also in the Workflow at the top
    for step in workflow.flowdef:
        if not any([step.module == module.name for module in workflow.modules]):
            raise ValueError(f"Module {step.module} not in flow modules")

    # Validate that all the modules listed in the workflow are also in the workcell
    [find_step_module(workcell, module.name) for module in workflow.modules]
