"""A Class to represent a workcell object that contains the different WEI modules"""
import logging
from typing import Any, Dict, Optional

from rpl_wei.core import DATA_DIR
from rpl_wei.core.data_classes import Module
from rpl_wei.core.data_classes import Workcell as WorkcellData
from rpl_wei.core.loggers import WEI_Logger


class Workcell:
    """A Class to represent a workcell object that contains the different WEI modules"""

    def __init__(
        self, workcell: WorkcellData=None, workcell_def: Dict[str, Any]=None, log_level: int = logging.INFO
    ) -> None:
        """Defines a workcell object loaded from a yaml file

        Parameters
        ----------
        workcell_def: Dict[str, Any]
           data from workcell yaml file

        log_level: int
            level for logging

        """
        if workcell_def: 
            self.workcell = WorkcellData(**workcell_def)
        else: 
            self.workcell = workcell
        self.log_dir = DATA_DIR / "workcell"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.locations = self.workcell.locations
        # TODO redo logger with ULID (and workcell hash?) https://pypi.org/project/python-ulid/
        self.wc_logger = WEI_Logger.get_logger(
            "wcLogger",
            log_dir=self.log_dir,
            log_level=log_level,
        )

    def __repr__(self) -> str:
        """representation of the workcell

        Parameters
        ----------
        None

        Returns
        -------
        str
            a string representation of the workcell
        """
        return self.workcell.__repr__()

    def find_step_module(self, step_module: str) -> Optional[Module]:
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
        for module in self.workcell.modules:
            module_name = module.name
            if module_name == step_module:
                return module

        return None
