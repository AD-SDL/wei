"""Abstraction of a singular workflow. Wei client interacts with this to run workflows"""
import logging
from pathlib import Path
from typing import Any, List, Optional

from devtools import debug

from rpl_wei.data_classes import Module, PathLike, WorkCell, Workflow
from rpl_wei.executors import StepExecutor
from rpl_wei.validators import ModuleValidator, StepValidator


class WF_Client:
    """Class for interacting with a specific workflow"""

    def __init__(
        self,
        wf_config: Path,
        wc_config: Optional[Path] = None,
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

        if wc_config:
            wc_config = wc_config.expanduser().resolve()
            # if relative path used, resolve
            if not self.workflow.workcell.is_absolute():
                self.workflow.workcell = (
                    (wf_config.parent / self.workflow.workcell).expanduser().resolve()
                )

            # match the wc_config and workflow.workcell files, make sure they are the same
            if not self.workflow.workcell.samefile(wc_config):
                raise ValueError(
                    f"Workcell file from workcell ({self.workflow.workcell}) is not the same file as the workcell from WEI ({wc_config})"
                )
        else:
            if not self.workflow.workcell.is_absolute():
                self.workflow.workcell = (
                    (wf_config.parent / self.workflow.workcell).expanduser().resolve()
                )
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
            # get module information from workcell file
            step_module = self._find_step_module(step.module)
            if not step_module:
                raise ValueError(
                    f"No module found for step module: {step.module}, in step: {step}"
                )

            # replace location names with actual locations
            if "source" in step.args:
                source_locator = step.args["source"]  # ot2_pcr_alpha.positions.deck2
                target_locator = step.args["target"]
                if type(source_locator) == str:
                    split_source = source_locator.split(".")
                    source_module = self._find_step_module(split_source[0])
                    if not source_module:
                        raise ValueError(
                            f"Source module not found for step: {step}, source: {source_locator}"
                        )
                    assert split_source[1] == "positions"
                    source_locator = source_module.positions[split_source[2]]
                if type(target_locator) == str:
                    split_target = target_locator.split(".")
                    target_module = self._find_step_module(split_target[0])
                    if not target_module:
                        raise ValueError(
                            f"Targe module not found for step: {step}, target: {target_locator}"
                        )
                    assert split_target[1] == "positions"
                    target_locator = target_module.positions[split_target[2]]

                step.args["source"] = source_locator
                step.args["target"] = target_locator

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
