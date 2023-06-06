from pathlib import Path
from typing import Dict, Optional

import requests

class Events():
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

        
    def _return_response(self, response: requests.Response):
        if response.status_code != 200:
            return {"http_error": response.status_code}

        return response.json()    
    def decision(self, dec_name: str, dec_value):
        url = f"{self.url}/log/{self.experiment_id}"

        response = requests.post(
            url,
            params={
                "log_value": "Checked " + dec_name + " with result " + str(dec_value)
            },
        )
        return self._return_response(response)

    def loop_start(self, loop_name: str):
        url = f"{self.url}/log/{self.experiment_id}"
        self.loops.append(loop_name)
        response = requests.post(
            url,
            params={"log_value": "LOOP:START: " + loop_name},
        )
        return self._return_response(response)

    def loop_end(self):
        url = f"{self.url}/log/{self.experiment_id}"
        loop_name = self.loops.pop()
        response = requests.post(url, params={"log_value": "LOOP:END: " + loop_name})
        return self._return_response(response)

    def loop_check(self, condition, value):
        url = f"{self.url}/log/{self.experiment_id}"
        loop_name = self.loops[-1]
        response = requests.post(
            url,
            params={
                "log_value": "LOOP:CHECK CONDITION: "
                + loop_name
                + ", CONDITION: "
                + condition
                + ", RESULT: "
                + str(value)
            },
        )

        return self._return_response(response)