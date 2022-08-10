"""Interaction point for user to the RPL workcells/flows"""
from argparse import ArgumentParser
from pathlib import Path

from devtools import debug

from rpl_wei.data_classes import WorkCell, Workflow


class WEI:
    """Client to interact with a workflow"""

    def __init__(self, wc_config_file):
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

    def check_modules(self):
        """Checks the modules required by the workflow"""
        for module in self.modules:
            print(f"Checking module: {module}")

    def check_flowdef(self):
        """Checks the actions provided by the workflow"""
        for step in self.flowdef:
            print(f"Checking step: {step}")

    def run_flow(self):
        """Executes the flowdef commmands"""

        for step in self.flowdef:
            print(step)

    def print_flow(self):
        """Prints the workflow dataclass, for debugging"""
        debug(self.workflow)

    def print_workcell(self):
        """Print the workcell datacall, for debugging"""
        debug(self.workcell)


def main(args):  # noqa: D103
    wc = WEI(args.workflow)
    if args.verbose:
        wc.print_flow()
        wc.print_workcell()
    wc.check_modules()
    wc.check_flowdef()


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-wf", "--workflow", help="Path to workflow file", type=Path, required=True)
    parser.add_argument("-v", "--verbose", help="Extended printing options", action="store_true")

    args = parser.parse_args()
    main(args)
