"""Contains the Events class for logging experiment steps"""

from typing import Any, Dict, Optional

import requests

from wei.config import Config
from wei.core.data_classes import BaseModel, Step, WorkflowRun
from wei.core.loggers import WEI_Logger


class Event(BaseModel):
    """A single event in an experiment"""

    experiment_id: str
    event_type: str
    event_name: str
    event_info: Optional[Any] = None


class EventLogger:
    """Registers Events during the Experiment execution both in a logfile and on Kafka"""

    def __init__(
        self,
        experiment_id: str,
    ) -> None:
        """Initializes an Event Logging object

        Parameters
        ----------
        experiment_id: str
            Programmatically generated experiment id, can be reused if needed

        Returns
        ----------
        None
        """
        self.experiment_id = experiment_id
        self.kafka_topic = "wei_diaspora"

        if Config.use_diaspora:
            try:
                from diaspora_event_sdk import Client, KafkaProducer, block_until_ready

                assert block_until_ready()
                self.kafka_producer = KafkaProducer()
                print("Creating Diaspora topic: %s", self.kafka_topic)
                c = Client()
                assert c.register_topic(self.kafka_topic)["status"] in [
                    "success",
                    "no-op",
                ]
            except Exception as e:
                print(e)
                print(
                    "Failed to connect to Diaspora or create topic. Have you registered it already?"
                )
        else:
            self.kafka_producer = None
            self.kafka_topic = None

    def log_event(self, log_value: Event) -> Dict[Any, Any]:
        """logs an event in the proper place for the given experiment

        Parameters
        ----------
        log_value : str
            the specifically formatted value to log

        Returns
        -------
        None
        """
        logger = WEI_Logger.get_experiment_logger(self.experiment_id)
        logger.info(log_value.model_dump_json())

        if self.kafka_producer:
            try:
                future = self.kafka_producer.send(
                    self.kafka_topic, log_value.model_dump(mode="json")
                )
                print(future.get(timeout=10))
            except Exception as e:
                print(str(e))


class Events:
    """An interface for logging events"""

    def __init__(
        self,
        server_addr: str,
        server_port: str,
        experiment_id: str,
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
        """
        self.server_addr = server_addr
        self.server_port = server_port
        self.experiment_id = experiment_id
        self.url = f"http://{self.server_addr}:{self.server_port}"

    def _log_event(
        self, event_type: str, event_name: str, event_info: Optional[Any] = ""
    ) -> Dict[Any, Any]:
        """logs an event in the proper place for the given experiment

        Parameters
        ----------
        log_value : str
            the specifically formatted value to log

        Returns
        -------
        response: Dict
           The JSON portion of the response from the server"""

        url = f"{self.url}/events/"
        event = Event.model_validate(
            {
                "experiment_id": self.experiment_id,
                "event_type": event_type,
                "event_name": event_name,
                "event_info": event_info,
            }
        )
        response = requests.post(
            url,
            json=event.model_dump(mode="json"),
        )
        if response.ok:
            return response.json()
        else:
            response.raise_for_status()

    def start_experiment(self) -> Dict[Any, Any]:
        """logs the start of a given experiment

        Returns
        -------
        response: Dict
           The JSON portion of the response from the server"""

        return self._log_event("EXPERIMENT", "START")

    def end_experiment(self) -> Dict[Any, Any]:
        """logs the end of an experiment

        Returns
        -------
        response: Dict
           The JSON portion of the response from the server"""
        return self._log_event("EXPERIMENT", "END")

    def log_decision(self, dec_name: str, dec_value: bool) -> Dict[Any, Any]:
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

    def log_comment(self, comment: str) -> Dict[Any, Any]:
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

    def log_local_compute(self, func_name: str) -> Dict[Any, Any]:
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

    def log_globus_compute(self, func_name: str) -> Dict[Any, Any]:
        """logs a function running using Globus Compute

        Parameters
        ----------
        func_name : str
            the name of the function run

        -------
        response: Dict
           The JSON portion of the response from the server"""
        return self._log_event("GLOBUS", "COMPUTE", {"function_name": func_name})

    def log_globus_flow(self, flow_name: str, flow_id: Any) -> Dict[Any, Any]:
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
        return self._log_event(
            "GLOBUS",
            "GLADIER_RUNFLOW",
            {"flow_name": flow_name, "flow_id": str(flow_id)},
        )

    def log_loop_start(self, loop_name: str) -> Dict[Any, Any]:
        """logs the start of a loop during an Experiment

        Parameters
        ----------
        loop_name : str
            A name describing the loop run

        Returns
        -------
        response: Dict
           The JSON portion of the response from the server"""
        return self._log_event("LOOP", "START", {"loop_name": loop_name})

    def log_loop_end(self, loop_name: str) -> Dict[Any, Any]:
        """Pops the most recent loop from the loop stack and logs its completion


        Returns
        -------
        response: Dict
           The JSON portion of the response from the server"""
        return self._log_event("LOOP", "END", {"loop_name": loop_name})

    def log_loop_check(
        self, condition: Any, value: Any, loop_name: str
    ) -> Dict[Any, Any]:
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
        return self._log_event(
            "LOOP",
            "CHECK CONDITION",
            {"loop_name": loop_name, "condition": condition, "result": str(value)},
        )

    def log_wf_queued(self, wf_name: str, run_id: str) -> Dict[Any, Any]:
        """Logs when a workflow is queued


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
            "WEI", "WORKFLOW_QUEUED", {"wf_name": str(wf_name), "run_id": str(run_id)}
        )

    def log_wf_start(self, wf_name: str, run_id: str) -> Dict[Any, Any]:
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

    def log_wf_failed(self, wf_name: str, run_id: str) -> Dict[Any, Any]:
        """Logs a failed workflow


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
            "WEI", "WORKFLOW_FAILED", {"wf_name": str(wf_name), "run_id": str(run_id)}
        )

    def log_wf_step(self, wf_run: WorkflowRun, step: Step) -> Dict[Any, Any]:
        """Logs a step in a workflow"""
        return self._log_event(
            "WEI",
            "WORKFLOW_STEP",
            {
                "wf_name": str(wf_run.name),
                "run_id": str(wf_run.run_id),
                "step_name": str(step.name),
                "step_id": str(step.id),
                "step_index": str(wf_run.step_index),
                "result": step.result.model_dump(mode="json"),
            },
        )

    def log_wf_end(self, wf_name: str, run_id: str) -> Dict[Any, Any]:
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
