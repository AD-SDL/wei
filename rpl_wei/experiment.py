import requests
from pathlib import Path
from typing import Dict, Optional
import ulid
from rpl_wei.core.loggers import WEI_Logger

class Experiment:
    def __init__(self, server_addr: str, server_port: str, experiment_name: str, experiment_id: Optional[str] = None) -> None:
        self.server_addr = server_addr
        self.server_port = server_port
        self.experiment_id = experiment_id
        self.experiment_name = experiment_name
        self.url = f"http://{self.server_addr}:{self.server_port}"
        self.loops = []
        if not self.experiment_id:
            self.experiment_id = ulid.new().str


    def _return_response(self, response: requests.Response):
        if response.status_code != 200:
            return {"http_error": response.status_code}

        return response.json()

    def run_job(self, workflow_file: Path, payload: Optional[Dict] = None):
        assert workflow_file.exists(), f"{workflow_file} does not exist"

        url = f"{self.url}/job"
        with open(workflow_file, "rb") as f:
            response = requests.post(
                url,
                params={"experiment_id": self.experiment_id, "payload": payload},
                files={"workflow": (str(workflow_file), f, "application/x-yaml")}
            )

        return self._return_response(response)
    
    def register_exp(self):
        url = f"{self.url}/experiment"
        
        response = requests.post(
                url,
                params={"experiment_id": self.experiment_id, "experiment_name": self.experiment_name},
                
            )

        return self._return_response(response)
    def log_decision(self, dec_name: str, dec_value):
        url = f"{self.url}/log/{self.experiment_id}"
        
        response = requests.post(
                url,
                params={"log_value": "Checked "+ dec_name + " with result "+ str(dec_value)},
                
            )

        return self._return_response(response)
    def start_loop(self, loop_name: str):
        url = f"{self.url}/log/{self.experiment_id}"
        self.loops.append(loop_name)
        response = requests.post(
                url,
                params={"log_value": "Start Loop: " + loop_name},
                
            )

        return self._return_response(response)
    def end_loop(self):
        url = f"{self.url}/log/{self.experiment_id}"
        loop_name = self.loops.pop()
        response = requests.post(
                url,
                params={"log_value": "End Loop: " + loop_name},
                
            )

        return self._return_response(response)
    def loop_check(self, condition, value):
        url = f"{self.url}/log/{self.experiment_id}"
        loop_name = self.loops[-1]
        response = requests.post(
                url,
                params={"log_value": "Check Loop: " + loop_name + ", Condition: "+ condition + ", Result: " + str(value)},
                
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
