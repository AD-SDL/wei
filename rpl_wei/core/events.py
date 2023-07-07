"""Contains the Events class for logging experiment steps"""
from typing import Optional

import requests


class Events:
    """Registers Events during the Experiment execution both in a cloud log and eventually on Kafka"""

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
        """processes the response of a Post request

        Parameters
        ----------
        response : requests.Response
            A response from an http Post request

        Returns
        -------
        Any
           The JSON portion of the request"""
        if response.status_code != 200:
            return {"http_error": response.status_code}

        return response.json()

    def _log_event(self, log_value: str):
        """logs an event in the proper place for the given experiment

        Parameters
        ----------
        log_value : str
            the specifically formatted value to log

        Returns
        -------
        Any
           The JSON portion of the response from the server"""
        url = f"{self.url}/log/{self.experiment_id}"

        response = requests.post(
            url,
            params={"log_value": log_value},
        )
        kafka = False
        if kafka:
            from kafka import KafkaProducer

            producer = KafkaProducer(
                bootstrap_servers="ec2-54-160-200-147.compute-1.amazonaws.com:9092"
            )
            producer.send(log_value, b"some_message_bytes")

        return self._return_response(response)

    def decision(self, dec_name: str, dec_value: bool):
        """logs an event in the proper place for the given experiment

        Parameters
        ----------
        dec_name : str
            a description of the decision being made
        dec_value: bool
            the boolean value of that decision.
        Returns
        -------
        Any
           The JSON portion of the response from the server"""
        return self._log_event("CHECK:" + str(dec_value).capitalize() + ": " + dec_name)

    def comment(self, comment: str):
        """logs a comment on the run
        Parameters
        ----------
        comment: str
            the comment to be looged
        Returns
        -------
        Any
           The JSON portion of the response from the server"""
        return self._log_event(comment)

    def log_local_compute(self, func_name):
        """Logs a local function running on the system.
        Parameters
        ----------
        func_name : str
            the name of the function run

        Returns
        -------
        Any
           The JSON portion of the response from the server"""

        return self._log_event("LOCAL:COMPUTE: " + func_name)

    def log_globus_compute(self, func_name):
        """logs a function running using Globus Compute

        Parameters
        ----------
        func_name : str
            the name of the function run

        Returns
        -------
        Any
           The JSON portion of the response from the server"""
        return self._log_event("GLOBUS:COMPUTE: " + func_name)

    def log_gladier(self, flow_name: str, flow_id):
        """logs a function running using Globus Gladier

        Parameters
        ----------
        flow_name : str
            the name of the flow run
        flow_id : str
            the id generated by Gladier for the flow

        Returns
        -------
        Any
           The JSON portion of the response from the server"""
        return self._log_event(
            "GLOBUS:GLADIER:RUNFLOW:" + flow_name + " with ID " + flow_id
        )

    def loop_start(self, loop_name: str):
        """logs the start of a loop during an Experimet

        Parameters
        ----------
        loop_name : str
            A name describing the loop run

        Returns
        -------
        Any
           The JSON portion of the response from the server"""
        self.loops.append(loop_name)
        return self._log_event("LOOP:START:" + loop_name)

    def loop_end(self):
        """Pops the most recent loop from the loop stack and logs its completion


        Returns
        -------
        Any
           The JSON portion of the response from the server"""
        loop_name = self.loops.pop()
        return self._log_event("LOOP:END:" + loop_name)

    def loop_check(self, condition, value):
        """Peeks the most recent loop from the loop stack and logs its completion


        Parameters
        ----------
        condition : str
            A value describing the condition being checked to see if the loop will continue.

        value: bool
            Whether or not the condition was met.

        Returns
        -------
        Any
           The JSON portion of the response from the server"""
        loop_name = self.loops[-1]
        return self._log_event(
            "LOOP:CHECK CONDITION: "
            + loop_name
            + ", CONDITION: "
            + condition
            + ", RESULT: "
            + str(value)
        )
