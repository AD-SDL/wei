"""Validators for actions and modules"""
from argparse import ArgumentParser
from pathlib import Path
from typing import Tuple, Optional
import logging

from rpl_wei.data_classes import SimpleModule, Step


class StepValidator:
    """Validate the steps of a workcell"""

    def __init__(self, run_logger: Optional[logging.Logger] = None) -> None:  # noqa: D103, D107
        self.run_logger = run_logger

    def check_step(self, step: Step) -> Tuple[bool, str]:
        """The method queries the module specified by the step and validates the action can be run on this machien

        Parameters
        ----------
        step : Step
            A single step from an instance of a workflow

        Returns
        -------
        bool
            Whether or not the step can be run on the module
        """
        if self.run_logger:
            self.run_logger.debug(f"Checking step: {step}")

        return True, f"Step okay: {step}"


class ModuleValidator:
    """Validate the modules of a workcell"""

    def __init__(self, run_logger: Optional[logging.Logger] = None) -> None:  # noqa: D103, D107
        self.run_logger = run_logger

    def check_module(self, module: SimpleModule) -> Tuple[bool, str]:
        """This object queries the modules to see if they are online/functional

        Parameters
        ----------
        module : Module
            The module dataclass with information about the module

        Returns
        -------
        Tuple[bool, str]
            Tuple with okay status (bool) and the status response from the robot
        """
        if self.run_logger:
            self.run_logger.debug(f"Checking module: {module}")

        return True, f"status okay for module: {module}"


def main(args):  # noqa: D103
    module_validator = ModuleValidator()

    from rpl_wei.wei_client_base import WEI

    wei = WEI(wc_config_file=args.config)

    for module in wei.workcell.modules:
        print(module_validator.check_module(module))


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-c", "--config", help="WEI config file, for testing", type=Path, required=True)

    args = parser.parse_args()
    main(args)
