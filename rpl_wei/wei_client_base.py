"""Interaction point for user to the RPL workcells/flows"""
import logging
from argparse import ArgumentParser
from pathlib import Path

from devtools import debug

from rpl_wei.data_classes import PathLike, WorkCell, Workflow
from rpl_wei.validation import ModuleValidator, StepValidator
from rpl_wei.execution import StepExecutor


class WEI:
    """Client to interact with a workflow"""

    def __init__(
        self,
        wc_config_file,
        log_dir: Path = Path("./logs"),
        workcell_log_level: int = logging.INFO,
        workflow_log_level: int = logging.INFO,
    ):
        """Initialize a workflow client

        Parameters
        ----------
        wc_config_file : Pathlike
            The workflow config path
        """
        self.state = None

        self.workflow = Workflow.from_yaml(wc_config_file)
        self.modules = self.workflow.modules
        self.flowdef = self.workflow.flowdef
        self.workcell = WorkCell.from_yaml(self.workflow.workcell)

        # Setup loggers
        log_dir.mkdir(exist_ok=True)
        run_log_dir = log_dir / "runs/"
        run_log_dir.mkdir(exist_ok=True)
        self.log_dir = log_dir
        self.run_log_dir = run_log_dir

        self.run_id = self.workflow.id
        self._setup_logger(
            "wcLogger",
            log_dir / f"{Path(self.workflow.workcell).stem}.log",
            level=workcell_log_level,
        )
        self._setup_logger("runLogger", run_log_dir / f"run-{self.run_id}.log", level=workflow_log_level)

        self.run_logger = self._get_logger("runLogger")
        self.wc_logger = self._get_logger("wcLogger")

        # Setup validators
        self.module_validator = ModuleValidator()
        self.step_validator = StepValidator()

        # Setup executor
        self.executor = StepExecutor(self.run_logger)

    def _setup_logger(self, logger_name: str, log_file: PathLike, level: int = logging.INFO):
        logger = logging.getLogger(logger_name)
        formatter = logging.Formatter("%(asctime)s %(levelname)s : %(message)s")
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

    def run_flow(self):
        """Executes the flowdef commmands"""

        # Log start time of the run
        self.wc_logger.info(f"Starting workflow run {self.run_id}")

        # TODO: Eventually pull this into the `execution.py` StepExecutor class
        # Make sure to get the necesary logging and what not
        # Start executing the step
        for step in self.flowdef:
            self.executor.execute_step(step)

        # Log the finish time of the run
        self.wc_logger.info(f"Completed workflow run {self.run_id}")

    def print_flow(self):
        """Prints the workflow dataclass, for debugging"""
        debug(self.workflow)

    def print_workcell(self):
        """Print the workcell datacall, for debugging"""
        debug(self.workcell)


def main(args):  # noqa: D103
    wei = WEI(
        args.workflow,
        workcell_log_level=logging.DEBUG,
        workflow_log_level=logging.DEBUG,
    )
    if args.verbose:
        wei.print_flow()
        wei.print_workcell()
    wei.check_modules()
    wei.check_flowdef()

    wei.run_flow()


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-wf", "--workflow", help="Path to workflow file", type=Path, required=True)
    parser.add_argument("-v", "--verbose", help="Extended printing options", action="store_true")

    args = parser.parse_args()
    main(args)
