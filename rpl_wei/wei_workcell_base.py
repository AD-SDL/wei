"""Interaction point for user to the RPL workcells/flows"""
import logging
from argparse import ArgumentParser
from pathlib import Path
from typing import Callable, Dict, List, Optional, Any

from rpl_wei.data_classes import WorkCell
from rpl_wei.publishers import PilotPublisher
from rpl_wei.wei_workflow_base import WF_Client
from rpl_wei.loggers import WEI_Logger


class WEI:
    """Client to interact with a workcell/group of workflows

    A group can be one element but this class is designed to work with a workcell/workflow pair
    """

    def __init__(
        self,
        wf_config: Path,
        workcell_log_level: int = logging.INFO,
        workflow_log_level: int = logging.INFO,
    ) -> None:
        """Initialize a WEI client

        Parameters
        ----------
        wf_configs : Path
            path to the config folder
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
        self.log_base = Path.home() / ".wei"
        self.log_dir = self.log_base / wf_config.stem
        self.log_dir.mkdir(exist_ok=True, parents=True)

        self.wc_logger = WEI_Logger.get_logger(
            "wcLogger",
            log_dir=self.log_dir,
            log_level=self.workcell_log_level,
        )

        self.wc_cofig_path = wf_config
        self.workflow = WF_Client(
            wf_config,
            log_dir=self.log_dir,
            workflow_log_level=self.workflow_log_level,
        )
        self.run_history = {}

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
        return self.workflow.workcell

    def run_workflow(
        self,
        callbacks: Optional[List[Callable]] = None,
        payload: Dict = None,
        publish: bool = False,
    ) -> Optional[bool]:
        """Run a workflow with a given workflow ID

        Parameters
        ----------
        workflow_id : Optional[UUID], optional
            The workflow ID you would like to run, by default None
        """

        self.wc_logger.info(f"Starting run with payload: {payload}")
        run_info = self.workflow.run_flow(callbacks, payload=payload)
        run_id = run_info["run_id"]
        self.wc_logger.info(
            f"Completed run with run id: {run_id} and payload: {payload}"
        )

        run_info["payload"] = payload
        self.run_history[run_id] = run_info
        if publish:
            # TODO this is not the right param
            PilotPublisher.publish(run_info)

        return run_info

    def get_workflow_results(self, run_id: str) -> Optional[Dict[str, Any]]:
        return self.run_history.get(run_id, None)


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
