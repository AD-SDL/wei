"""A Class to represent a workcell object that contains the different WEI modules"""
from pathlib import Path
from typing import Optional

import yaml

from wei.config import Config
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

    raise ValueError(f"Module {step_module} not in Workcell {workcell.name}")


def load_workcell_file(workcell_file: Path) -> WorkcellData:
    """Loads a workcell file and returns a WorkcellData object

    Parameters
    ----------
    workcell_file : Path
        The path to the workcell file

    Returns
    -------
    workcell: WorkcellData
        The workcell object
    """
    with open(workcell_file, "r") as f:
        workcell = WorkcellData(**yaml.safe_load(f))
    Config.workcell_file = workcell_file
    Config.workcell_name = workcell.name
    for property in workcell.config.model_dump(mode="python"):
        setattr(Config, property, getattr(workcell.config, property))

    return workcell
