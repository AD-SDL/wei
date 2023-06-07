from pathlib import Path
from typing import Dict, Optional

import requests


class Events:
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

    def _return_response(self, response: requests.Response):
        if response.status_code != 200:
            return {"http_error": response.status_code}

        return response.json()

    def _log_event(self, log_value: str):
        url = f"{self.url}/log/{self.experiment_id}"

        response = requests.post(
            url,
            params={"log_value": log_value},
        )
        return self._return_response(response)

    def decision(self, dec_name: str, dec_value):

        return self._log_event("CHECK:"+ str(dec_value).capitalize() +": " + dec_name)
    
    def log_local_compute(self, func_name):

        return self._log_event("LOCAL:COMPUTE: "+ func_name)
    
    def log_globus_compute(self, func_name):

        return self._log_event("GLOBUS:COMPUTE: "+ func_name)
    
    def log_gladier(self, flow_name: str, flow_id):
        return self._log_event("GLOBUS:GLADIER:RUNFLOW:" + flow_name + " with ID " + flow_id)
    
    def loop_start(self, loop_name: str):
        url = f"{self.url}/log/{self.experiment_id}"
        self.loops.append(loop_name)
        return self._log_event("LOOP:START:" + loop_name)

    def loop_end(self):
        url = f"{self.url}/log/{self.experiment_id}"
        loop_name = self.loops.pop()
        return self._log_event("LOOP:END:" + loop_name)
        

    def loop_check(self, condition, value):
        url = f"{self.url}/log/{self.experiment_id}"
        loop_name = self.loops[-1]
        return self._log_event("LOOP:CHECK CONDITION: "
                + loop_name
                + ", CONDITION: "
                + condition
                + ", RESULT: "
                + str(value))
