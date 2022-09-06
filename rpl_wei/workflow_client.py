import logging
from pathlib import Path
from typing import Any, Optional, List

from devtools import debug

from rpl_wei.data_classes import Module, PathLike, WorkCell, Workflow
from rpl_wei.validation import ModuleValidator, StepValidator
from rpl_wei.execution import StepExecutor


class WF_Client:
    """Class for interacting with a specific workflow"""

    def __init__(
        self,
        wf_config: Path,
        log_dir: Optional[Path] = None,
        workflow_log_level: int = logging.INFO,
    ):
        """Initialize a workflow client

        Parameters
        ----------
        wc_config_file : Pathlike
            The workflow config path
        """

        self.workflow = Workflow.from_yaml(wf_config)
        self.modules = self.workflow.modules
        self.flowdef = self.workflow.flowdef
        self.workcell = WorkCell.from_yaml(self.workflow.workcell)

        # Setup loggers
        run_log_dir = log_dir / "runs/"
        run_log_dir.mkdir(exist_ok=True)
        self.log_dir = log_dir
        self.run_log_dir = run_log_dir

        self.run_id = self.workflow.id
        self._setup_logger(
            "runLogger",
            run_log_dir / f"run-{self.run_id}.log",
            level=workflow_log_level,
        )

        self.run_logger = self._get_logger("runLogger")

        # Setup validators
        self.module_validator = ModuleValidator()
        self.step_validator = StepValidator()

        # Setup executor
        self.executor = StepExecutor(self.run_logger)

    def _setup_logger(
        self, logger_name: str, log_file: PathLike, level: int = logging.INFO
    ):
        logger = logging.getLogger(logger_name)
        formatter = logging.Formatter("%(asctime)s (%(levelname)s): %(message)s")
        fileHandler = logging.FileHandler(log_file, mode="a+")
        fileHandler.setFormatter(formatter)
        streamHandler = logging.StreamHandler()
        streamHandler.setFormatter(formatter)

        logger.setLevel(level)
        logger.addHandler(fileHandler)
        logger.addHandler(streamHandler)

    def _get_logger(self, log_name: str) -> logging.Logger:
        return logging.getLogger(log_name)

    def check_modules(self):
        """Checks the modules required by the workflow"""
        for module in self.modules:
            self.module_validator.check_module(module=module)

    def check_flowdef(self):
        """Checks the actions provided by the workflow"""
        for step in self.flowdef:
            self.step_validator.check_step(step=step)

    def run_flow(self, callbacks: Optional[List[Any]] = None):
        """Executes the flowdef commmands"""

        # Start executing the steps
        for step in self.flowdef:
            # find the module
            step_module = self._find_step_module(step.module)
            if not step_module:
                raise ValueError(f"No module found for step module: {step.module}, in step: {step}")
            # execute the step
            self.executor.execute_step(step, step_module, callbacks=callbacks)

    def _find_step_module(self, step_module: str) -> Optional[Module]:

        for module in self.workcell.modules:
            module_name = module.name
            if module_name == step_module:
                return module

        return None

    def print_flow(self):
        """Prints the workflow dataclass, for debugging"""
        debug(self.workflow)

    def print_workcell(self):
        """Print the workcell datacall, for debugging"""
        debug(self.workcell)
