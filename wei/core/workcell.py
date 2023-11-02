"""A Class to represent a workcell object that contains the different WEI modules"""
from typing import Optional

from wei.core.data_classes import Module, WorkcellData


def find_step_module(workcell: WorkcellData, step_module: str) -> Optional[Module]:
    """finds the full module information based on just it's name

    Parameters
    ----------
    step_module : str
        the name of the module
    Returns
    -------
    module: Module
        The class with full information about the given module
    """
    for module in workcell.modules:
        module_name = module.name
        if module_name == step_module:
            return module

    raise ValueError(f"Module {module} not in Workcell {workcell.name}")
