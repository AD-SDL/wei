"""Abstraction of a singular workflow. Wei client interacts with this to run workflows"""
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

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

            # TODO: Add flow_id and flow_name to self

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

        # cache filenames for globus
        self.wf_file = wf_config
        self.wc_file = self.workflow.workcell

        # Setup loggers and results
        timestamp = datetime.now().strftime("%Y%m%d-%H%m%s")
        run_log_dir = log_dir / f"run-{timestamp}"
        run_log_dir.mkdir(exist_ok=True, parents=True)
        self.log_dir = log_dir
        self.run_log_dir = run_log_dir

        (run_log_dir / "results").mkdir(exist_ok=True, parents=True)

        self.run_id = self.workflow.id
        self._setup_logger(
            "runLogger",
            run_log_dir / "runlog.log",
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

    def run_flow(
        self,
        callbacks: Optional[List[Any]] = None,
        payload: Optional[Dict[str, Any]] = None,
    ):
        """Executes the flowdef commmands"""

        # Start executing the steps
        for step in self.flowdef:
            # get module information from workcell file
            step_module = self._find_step_module(step.module)
            if not step_module:
                raise ValueError(
                    f"No module found for step module: {step.module}, in step: {step}"
                )

            # replace position names with actual positions
            if isinstance(step.args, dict) and len(step.args) > 0:
                for key, value in step.args.items():
                    if hasattr(value, "__contains__") and "positions" in value:
                        module_name = value.split(".")[0]
                        module = self._find_step_module(module_name)

                        if not module:
                            raise ValueError(
                                f"Module positon not found for module '{module_name}' and identifier '{value}'"
                            )

                        location_varname = value.split(".")[-1]
                        assert (
                            location_varname in module.positions
                        ), f"Position {location_varname} not found"
                        location = module.positions[location_varname]

                        step.args[key] = location

            # Inject the payload
            if isinstance(payload, dict):
                if not isinstance(step.args, dict) or len(step.args) == 0:
                    continue

                (arg_keys, arg_values) = zip(*step.args.items())
                for key, value in payload.items():
                    if key in arg_values:
                        idx = arg_values.index(key)
                        step_arg_key = arg_keys[idx]
                        step.args[step_arg_key] = value

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
