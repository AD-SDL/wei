from pathlib import Path
from typing import Dict, Optional

import requests
import ulid
import json
from rpl_wei.core.events import Events


class Experiment:
    def __init__(
        self,
        server_addr: str,
        server_port: str,
        experiment_name: str,
        experiment_id: Optional[str] = None,
    ) -> None:
        self.server_addr = server_addr
        self.server_port = server_port
        self.experiment_id = experiment_id
        self.experiment_name = experiment_name
        self.url = f"http://{self.server_addr}:{self.server_port}"
        self.loops = []
        if not self.experiment_id:
            self.experiment_id = ulid.new().str
        self.events = Events(
            self.server_addr, self.server_port, self.experiment_name, self.experiment_id
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
        assert workflow_file.exists(), f"{workflow_file} does not exist"
        url = f"{self.url}/job"
        with open(workflow_file, "rb") as f:
            params = {
                "payload": json.dumps(payload),
                "experiment_id": self.experiment_id,
                "simulate": simulate,
            }

            response = requests.post(
                url,
                params=params,
                files={"workflow": (str(workflow_file), f, "application/x-yaml")},
            )

        return self._return_response(response)

    def register_exp(self):
        url = f"{self.url}/experiment"

        response = requests.post(
            url,
            params={
                "experiment_id": self.experiment_id,
                "experiment_name": self.experiment_name,
            },
        )

        return self._return_response(response)

    def query_job(self, job_id: str):
        url = f"{self.url}/job/{job_id}"
        response = requests.get(url)

        return self._return_response(response)

    def query_queue(self):
        url = f"{self.url}/queue/info"
        response = requests.get(url)

        if response.status_code != 200:
            return {"http_error": response.status_code}

        return self._return_response(response)
