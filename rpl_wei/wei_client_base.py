"""Interaction point for user to the RPL workcells/flows"""
import logging
from argparse import ArgumentParser
from pathlib import Path
from typing import Optional

from devtools import debug

from rpl_wei.data_classes import PathLike, WorkCell, Workflow
from rpl_wei.validation import ModuleValidator, StepValidator
from rpl_wei.execution import StepExecutor
from .workflow_client import WF_Client


class WEI:
    """Client to interact with a workcell/group of workflows

    A group can be one element but this class is designed to work with a workcell/workflow pair
    """

    def __init__(
        self,
        wf_configs: Path,
        log_dir: Optional[Path] = None,
        workcell_log_level: int = logging.INFO,
        workflow_log_level: int = logging.INFO,
    ) -> None:

        # TODO: need to figure out how to load when a user just gives us a file
        if wf_configs.is_file():
            # Setup logdir here
            pass

        # Setup log files
        if not log_dir:
            log_dir = wf_configs.parent / "logs/"

        log_dir.mkdir(exist_ok=True)

        # TODO: setup the wc logging
        # self._setup_logger("wcLogger", log_file=log_dir/f"{wc}")
        self.wc_logger = self._get_logger()

        self.workflows = {}
        for wf_path in wf_configs.glob("*[.yml][.yaml]"):
            wf = WF_Client(wf_path, log_dir, workflow_log_level=workflow_log_level)

            self.workflows[wf.run_id] = wf

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
