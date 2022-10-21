"""Interaction point for user to the RPL workcells/flows"""
import logging
from argparse import ArgumentParser
from pathlib import Path
from typing import Callable, Dict, List, Optional
from uuid import UUID

from rpl_wei.data_classes import PathLike, WorkCell, Workflow
from rpl_wei.wei_workflow_base import WF_Client


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
        """Initialize a WEI client

        Parameters
        ----------
        wf_configs : Path
            path to the config/config folder
        log_dir : Optional[Path], optional
            Path to the logdir, default None and will be created
        workcell_log_level : int, optional
            Python logging level for the workcell logs, by default logging.INFO
        workflow_log_level : int, optional
            Python logging level for the workflow logs, by default logging.INFO

        """
        self.workcell_log_level = workcell_log_level
        self.workflow_log_level = workflow_log_level

        # Setup log files
        # TODO this was originally wc_config, but since this is optional now this might
        #      have to be handled in the workflow_client.py
        if not log_dir:
            self.log_dir = wf_configs.parent / "logs/"
        else:
            if log_dir.is_file():
                self.log_dir = log_dir.parent
            else:
                self.log_dir = log_dir
        self.log_dir.mkdir(exist_ok=True, parents=True)

        # TODO this was originally wc_config, but since this is optional now this might
        #      might have be handled elsewhere
        self._setup_logger(
            "wcLogger",
            log_file=self.log_dir / f"{wf_configs.stem}.log",
            level=self.workcell_log_level,
        )
        self.wc_logger = self._get_logger(log_name="wcLogger")

        self.workflows = {}
        # User can pass us a single file or a directory of files
        if wf_configs.is_file():
            wf = WF_Client(
                wf_configs,
                log_dir=self.log_dir,
                workflow_log_level=self.workflow_log_level,
            )
            self.workflows[wf.run_id] = {"workflow": wf, "run": False}

        elif wf_configs.is_dir():
            # TODO: what if there is a specific order to run the workflows?
            for wf_path in wf_configs.glob("*[.yml][.yaml]"):
                wf = WF_Client(
                    wf_path, self.log_dir, workflow_log_level=self.workflow_log_level
                )

                self.workflows[wf.run_id] = {"workflow": wf, "run": False}

    @property
    def workcell(self) -> Optional[WorkCell]:
        """Return the workcell of a run

        As long as there is only one workflow then we cna return a run, otherwise we need to know what
        run we need the workcell for. This should be changed when we switch to the wc-has->wf model.

        Returns
        -------
        Optional[WorkCell]
            The workcell object if there is only one attatched to this client, otherwise None
        """
        if len(self.workflows) != 1:
            # more than one workflow present
            # Could check them all to see if same workflow?
            return None

        key = list(self.workflows.keys())[0]
        return self.workflows[key].get("workflow").workcell

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

    def run_workflow(
        self,
        workflow_id: Optional[UUID] = None,
        callbacks: Optional[List[Callable]] = None,
    ) -> None:
        """Run a workflow with a given workflow ID

        Parameters
        ----------
        workflow_id : Optional[UUID], optional
            The workflow ID you would like to run, by default None
        """
        if workflow_id:
            workflow: WF_Client = self.workflows[workflow_id]["workflow"]
            self.wc_logger.info(f"Starting run with run id: {workflow.run_id}")
            workflow.run_flow(callbacks)
            self.wc_logger.info(f"Completed run with run id: {workflow.run_id}")
            self.workflows[workflow_id]["run"] = True
        else:
            # TODO: Figure out what to do if they don't give a workflow id
            # TODO: What if there is a specific order to run flows
            pass

    def get_workflows(self) -> Dict:
        """Return all workflows. Gets the workflow id and its path

        Returns
        -------
        Dict
            The workflow dictionary, keys are UUID of the run, values are a path to the config file and
            whether or not it has been run (might contain more info later...)
        """
        return self.workflows

    def get_workflow(self, run_id: UUID) -> Workflow:
        """Get a workflow with a specific id

        Parameters
        ----------
        run_id : UUID
            The ID of the workflow you would like to retrieve

        Returns
        -------
        Workflow
            The workflow object which you can execute directly on
        """
        return self.workflows.get(run_id, None)

    def add_workflow(self, workflow_path: Path) -> None:
        """Add a workflow file to be run

        Parameters
        ----------
        workflow_path : Path
            Path to the new workflow file. Must use same workcell as this object
        """
        new_workflow = WF_Client(
            workflow_path, self.log_dir, workflow_log_level=self.workflow_log_level
        )

        self.workflows[new_workflow.run_id] = {"workflow": new_workflow, "run": False}


def main(args):  # noqa: D103
    wei = WEI(
        args.workflow,
        workcell_log_level=logging.DEBUG,
        workflow_log_level=logging.DEBUG,
    )

    # get the workflow id (currently defaulting to first one available)
    wf_id = list(wei.get_workflows().keys())[0]
    print(wei.get_workflows())

    wei.run_workflow(wf_id)

    print(f"Workflows present: {wei.get_workflows()}")


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-wc", "--workcell", help="Path to workcell file", type=Path)
    parser.add_argument(
        "-wf",
        "--workflow",
        help="Path to workflow directory or file",
        type=Path,
        required=True,
    )
    parser.add_argument(
        "-v", "--verbose", help="Extended printing options", action="store_true"
    )

    args = parser.parse_args()
    main(args)
