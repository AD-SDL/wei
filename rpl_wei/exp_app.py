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
    ) -> None:
        self.server_addr = server_addr
        self.server_port = server_port
        self.experiment_path = ""
        if experiment_id == None:
            self.experiment_id = ulid.new().str
        else:
            self.experiment_id = experiment_id
        self.experiment_name = experiment_name
        self.url = f"http://{self.server_addr}:{self.server_port}"
        self.loops = []
        if not self.experiment_id:
            self.experiment_id = ulid.new().str
        self.events = Events(
            self.server_addr,
            self.server_port,
            self.experiment_name,
            self.experiment_id,
            "ec2-54-160-200-147.compute-1.amazonaws.com:9092",
        )
        print(self.experiment_id)

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
        url = f"{self.url}/job"
        with open("/home/rpl/.wei/runs/payload.txt", "w") as f2:
            payload = json.dump(payload, f2)
            f2.close()
        with open(workflow_file, "rb") as (f):
            f2 = open("/home/rpl/.wei/runs/payload.txt", "rb")
            params = {

                "experiment_path": self.experiment_path,
                "simulate": simulate,
            }

            # print(params["payload"])
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
        print(self.experiment_id)
        self.experiment_path
        response = requests.post(
            url,
            params={
                "experiment_id": self.experiment_id,
                "experiment_name": self.experiment_name,
            },
        )
        print(response.json())
        self.experiment_path = response.json()["exp_dir"]

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

        url = f"{self.url}/job/{job_id}"
        response = requests.get(url)

        return self._return_response(response)
    def get_log(self):
        url = f"{self.url}/log/return"
        response = requests.get(url, params={"experiment_path": self.experiment_path})

        return self._return_response(response)
    def query_queue(self):
        url = f"{self.url}/queue/info"
        response = requests.get(url)

        if response.status_code != 200:
            return {"http_err   or": response.status_code}

        return self._return_response(response)
