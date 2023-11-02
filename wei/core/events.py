"""Contains the Events class for logging experiment steps"""

# import time

# from pathlib import Path
from typing import Any, Optional

import requests

from wei.core.experiment import log_experiment_event

# from diaspora_logger import DiasporaLogger

# def log_event_local():
#     return str(event.name, event)

# def log_event_kafka(event, producer):
#     producer.send(event, channel=event.experiment_id b"some_message_bytes")


class Events:
    """Registers Events during the Experiment execution both in a cloud log and eventually on Kafka"""

    def __init__(
        self,
        server_addr: str,
        server_port: str,
        experiment_id: Optional[str] = None,
        wei_internal: bool = False,
    ) -> None:
        """Initializes an Event Logging object

        Parameters
        ----------
        server_addr: str
            address for WEI server

        server_port: str
            port for WEI server

        experiment_name: str
            Human chosen name for experiment

        experiment_id: Optional[str]
            # Programmatically generated experiment id, can be reused if needed

        experiment_path: Optional[str]
            Path for logging the experiment on the server
        """
        self.server_addr = server_addr
        self.server_port = server_port
        self.experiment_id = experiment_id
        self.url = f"http://{self.server_addr}:{self.server_port}"
        self.wei_internal = wei_internal

        # switch to auth file at some point
        # with open(Path("/home/rpl/kafka.txt").resolve(), "r") as f:
        #     refresh_token = f.read()
        # print(refresh_token)
        # if not refresh_token:
        #     raise ValueError("Environment variable DIASPORA_REFRESH not set")

        # kafka_logger = DiasporaLogger(
        #     bootstrap_servers=["52.200.217.146:9093", "54.210.46.108:9094"],
        #     refresh_token=refresh_token,
        # )

        self.topic = "rpl_test"
        self.kafka_producer = None  # kafka_logger

        self.loops = []

    def _return_response(self, response: requests.Response):
        """processes the response of a Post request

        Parameters
        ----------
        response : requests.Response
            A response from an http Post request

        Returns
        -------
        response: Dict
           The JSON portion of the request"""
        if response.status_code != 200:
            return {"http_error": response.status_code}

        return response.json()

    def _log_event(
        self, event_type, event_name, event_info: Optional[Any] = "", log_dir=""
    ):
        """logs an event in the proper place for the given experiment

        Parameters
        ----------
        log_value : str
            the specifically formatted value to log

        Returns
        -------
        response: Dict
           The JSON portion of the response from the server"""
        url = f"{self.url}/exp/{self.experiment_id}/log"
        log_value = {
            "experiment_id": self.experiment_id,
            "event_type": event_type,
            "event_name": event_name,
            "event_info": event_info,
        }

        if self.wei_internal:
            log_experiment_event(self.experiment_id, str(log_value))
        else:
            response = requests.post(
                url,
                params={
                    "log_value": str(log_value),
                    "experiment_path": self.experiment_path,
                },
            )
        try:
            # self.kafka_producer.send(
            # self.topic,
            # log_value,
            # )
            pass

        except Exception as e:
            print(str(e))
            print("Kafka Unavailable")

        return self._return_response(response)

    def start_experiment(self):
        """logs the start of a given experiment

        Returns
        -------
        response: Dict
           The JSON portion of the response from the server"""

        return self._log_event("EXPERIMENT", "START")

    def end_experiment(self):
        """logs the end of an experiment

        Returns
        -------
        response: Dict
           The JSON portion of the response from the server"""
        return self._log_event("EXPERIMENT", "END")

    def log_decision(self, dec_name: str, dec_value: bool):
        """logs an decision in the proper place for the given experiment

        Parameters
        ----------
        dec_name : str
            a description of the decision being made
        dec_value: bool
            the boolean value of that decision.
        Returns
        -------
        response: Dict
           The JSON portion of the response from the server"""
        return self._log_event(
            "CHECK", dec_name.capitalize(), {"dec_value": str(dec_value)}
        )

    def log_comment(self, comment: str):
        """logs a comment on the run
        Parameters
        ----------
        comment: str
            the comment to be logged
        Returns
        -------
        response: Dict
           The JSON portion of the response from the server"""
        return self._log_event("COMMENT", comment)

    def log_local_compute(self, func_name):
        """Logs a local function running on the system.
        Parameters
        ----------
        func_name : str
            the name of the function run

        Returns
        -------
        response: Dict
           The JSON portion of the response from the server"""

        return self._log_event("LOCAL", "COMPUTE", {"function_name": func_name})

    def log_globus_compute(self, func_name):
        """logs a function running using Globus Compute

        Parameters
        ----------
        func_name : str
            the name of the function run

        -------
        response: Dict
           The JSON portion of the response from the server"""
        return self._log_event("GLOBUS", "COMPUTE", {"function_name": func_name})

    def log_globus_flow(self, flow_name: str, flow_id):
        """logs a function running using Globus Gladier

        Parameters
        ----------
        flow_name : str
            the name of the flow run
        flow_id : str
            the id generated by Gladier for the flow

        Returns
        -------
        response: Dict
           The JSON portion of the response from the server"""
        return self._log_event("GLOBUS", "GLADIER_RUNFLOW", {"flow_id": flow_id})

    def log_loop_start(self, loop_name: str):
        """logs the start of a loop during an Experiment

        Parameters
        ----------
        loop_name : str
            A name describing the loop run

        Returns
        -------
        response: Dict
           The JSON portion of the response from the server"""
        self.loops.append(loop_name)
        return self._log_event("LOOP", "START", {"loop_name": loop_name})

    def log_loop_end(self):
        """Pops the most recent loop from the loop stack and logs its completion


        Returns
        -------
        response: Dict
           The JSON portion of the response from the server"""
        loop_name = self.loops.pop()
        return self._log_event("LOOP", "END", {"loop_name": loop_name})

    def log_loop_check(self, condition, value):
        """Peeks the most recent loop from the loop stack and logs its completion


        Parameters
        ----------
        condition : str
            A value describing the condition being checked to see if the loop will continue.

        value: bool
            Whether or not the condition was met.

        Returns
        -------
        response: Dict
           The JSON portion of the response from the server"""
        loop_name = self.loops[-1]
        return self._log_event(
            "LOOP",
            "CHECK CONDITION",
            {"loop_name": loop_name, "condition": condition, "result": str(value)},
        )

    def log_wf_start(self, wf_name: str, run_id: str):
        """Logs the start of a workflow


        Parameters
        ----------
        wf_name : str
            The name of the workflow

        run_id: str
            The run_id of the workflow.

        Returns
        -------
        Any
           The JSON portion of the response from the server"""

        return self._log_event(
            "WEI", "WORKFLOW_START", {"wf_name": str(wf_name), "run_id": str(run_id)}
        )

    def log_wf_end(self, wf_name: str, run_id: str):
        """Logs the end of a workflow


        Parameters
        ----------
        wf_name : str
            The name of the workflow

        run_id: str
            The run_id of the workflow.

        Returns
        -------
        Any
           The JSON portion of the response from the server"""
        return self._log_event(
            "WEI", "WORKFLOW_END", {"wf_name": str(wf_name), "run_id": str(run_id)}
        )
