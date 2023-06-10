import logging
from typing import Any, Dict, Optional

from rpl_wei.core import DATA_DIR
from rpl_wei.core.data_classes import Module
from rpl_wei.core.data_classes import Workcell as WorkcellData
from rpl_wei.core.loggers import WEI_Logger


class Workcell:
    def __init__(
        self, workcell_def: Dict[str, Any], log_level: int = logging.INFO
    ) -> None:
        self.workcell = WorkcellData(**workcell_def)
        self.log_dir = DATA_DIR / "workcell"
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # TODO redo logger with ULID (and workcell hash?) https://pypi.org/project/python-ulid/
        self.wc_logger = WEI_Logger.get_logger(
            "wcLogger",
            log_dir=self.log_dir,
            log_level=log_level,
        )

    def __repr__(self) -> str:
        return self.workcell.__repr__()

    def find_step_module(self, step_module: str) -> Optional[Module]:
        for module in self.workcell.modules:
            module_name = module.name
            if module_name == step_module:
                return module

        return None
