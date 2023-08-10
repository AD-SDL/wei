"""Contains the Experiment class that manages WEI flows and helpes annotate the experiment run"""
import json
from pathlib import Path
from typing import Dict, Optional

import requests
import ulid

from rpl_wei.core.events import Events


class Experiment:
    """Methods for the running and logging of a WEI Experiment including running WEI workflows and logging"""

    def __init__(
        self,
        server_addr: str,
        server_port: str,
        experiment_name: str,
        experiment_id: Optional[str] = None,
        kafka_server: Optional[str] = None,
    ) -> None:
        """Initializes an Experiment, and creates its log files

        Parameters
        ----------
        server_addr: str
            address for WEI server

        server_port: str
            port for WEI server

        experiment_name: str
            Human chosen name for experiment

        experiment_id: Optional[str]
            Programatially generated experiment id, can be reused if needed

        kafka_server: Optional[str]
            Url of kafka server for logging
        """

        self.server_addr = server_addr
        self.server_port = server_port
        self.experiment_path = ""
        if experiment_id is None:
            self.experiment_id = ulid.new().str
        else:
            self.experiment_id = experiment_id
        self.experiment_name = experiment_name
        self.url = f"http://{self.server_addr}:{self.server_port}"
        self.kafka_server = kafka_server
        self.loops = []
        if not self.experiment_id:
            self.experiment_id = ulid.new().str
        self.events = Events(
            self.server_addr,
            self.server_port,
            self.experiment_name,
            self.experiment_id,
            kafka_server=self.kafka_server,
        )

    def _return_response(self, response: requests.Response):
        if response.status_code != 200:
            return {"http_error": response.status_code}

        return response.json()

    def run_job(
        self,
        workflow_file: Path,
        payload: Optional[Dict] = None,
        simulate: Optional[bool] = False,
    ):
        """Submits a workflow file to the server to be executed, and logs it in the overall event log.

        Parameters
        ----------
        workflow_file : str
           The path to the workflow file to be executed

        payload: bool
            The input to the workflow

        simulate: bool
            Whether or not to use real robots

        Returns
        -------
        Dict
           The JSON portion of the response from the server, including the ID of the job as job_id
        """
        assert workflow_file.exists(), f"{workflow_file} does not exist"
        url = f"{self.url}/job/run"
        payload_path = Path("~/.wei/temp/payload.txt")
        with open(payload_path.expanduser(), "w") as f2:
            payload = json.dump(payload, f2)
            f2.close()
        with open(workflow_file, "rb") as (f):
            f2 = open(payload_path.expanduser(), "rb")
            params = {
                "experiment_path": self.experiment_path,
                "simulate": simulate,
            }
            response = requests.post(
                url,
                params=params,
                json=payload,
                files={
                    "workflow": (str(workflow_file), f, "application/x-yaml"),
                    "payload": (str("payload_file.txt"), f2, "text"),
                },
            )

        return self._return_response(response)

    def register_exp(self):
        """Initializes an Experiment, and creates its log files

        Parameters
        ----------
        None

        Returns
        -------

        response: Dict
           The JSON portion of the response from the server"""
        url = f"{self.url}/experiment"
        response = requests.post(
            url,
            params={
                "experiment_id": self.experiment_id,
                "experiment_name": self.experiment_name,
            },
        )
        self.experiment_path = response.json()["exp_dir"]
        self.events.experiment_path = self.experiment_path
        return self._return_response(response)

    def query_job(self, job_id: str):
        """Checks on a workflow run using the id given

        Parameters
        ----------

        job_id : str
           The id returned by the run_job function for this run

        Returns
        -------

        response: Dict
           The JSON portion of the response from the server"""

        url = f"{self.url}/job/{job_id}/state"
        response = requests.get(url)

        return self._return_response(response)

    def get_job_log(self):
        """Returns the log for this experiment as a string

        Parameters
        ----------

        None

        Returns
        -------

        response: Dict
           The JSON portion of the response from the server with the experiment log"""
        url = f"{self.url}/log/return"
        response = requests.get(url, params={"experiment_path": self.experiment_path})

        return self._return_response(response)

    def query_queue(self):
        """Returns the queue info for this experiment as a string

        Parameters
        ----------

        None

        Returns
        -------

        response: Dict
           The JSON portion of the response from the server with the queue info"""
        url = f"{self.url}/queue/info"
        response = requests.get(url)

        if response.status_code != 200:
            return {"http_err   or": response.status_code}

        return self._return_response(response)
