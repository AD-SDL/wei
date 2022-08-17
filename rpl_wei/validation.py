"""Validators for actions and modules"""
from pathlib import Path
from argparse import ArgumentParser
from typing import Tuple

from rpl_wei.data_classes import Module


class ActionValidator:
    """Validate the actions of a workcell"""

    pass


class ModuleValidator:
    """Validate the modules of a workcell"""

    def __init__(self) -> None:
        pass

    def check_module(self, module: Module) -> Tuple[bool, str]:
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
        print(f"checking module: {module}")


def main(args):
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
