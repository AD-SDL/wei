"""Handling ZMQ execution for steps in the RPL-SDL efforts"""

import json
from typing import Any, Dict, Tuple

from wei.core.data_classes import Interface, Module, Step

try:
    import zmq  # type: ignore
except ImportError:
    print("Socket not found. Cannot use ZMQInterface")


class ZmqInterface(Interface):
    """Basic Interface for interacting with WEI modules using ZMQ"""

    @staticmethod
    def config_validator(config: Dict[str, Any]) -> bool:
        """Validates the configuration for the interface

        Parameters
        ----------
        config : dict
            The configuration for the module

        Returns
        -------
        bool
            Whether the configuration is valid or not
        """
        for key in ["zmq_node_address", "zmq_node_port"]:
            if key not in config:
                return False
        return True

    @staticmethod
    def send_action(step: Step, module: Module, **kwargs: Any) -> Tuple[str, str, str]:
        """Executes a single step from a workflow using a ZMQ messaging framework with the ZMQ library

        Parameters
        ----------
        step : Step
            A single step from a workflow definition

        Returns
        -------
        action_response: StepStatus
            A status of the step (in theory provides async support with IDLE, RUNNING, but for now is just SUCCEEDED/FAILED)
        action_msg: str
            the data or information returned from running the step.
        action_log: str
            A record of the execution of the step

        """
        context = zmq.Context()
        socket = context.socket(zmq.REQ)
        socket.connect(
            f"tcp://{module.config['zmq_node_address']}:{module.config['zmq_node_port']}"
        )

        msg = {
            "action_handle": step.action,
            "action_vars": step.args,
        }
        socket.send_string(json.dumps(msg))
        zmq_response = (
            socket.recv().decode()
        )  # does this need to be decoded with "utf-8"?
        zmq_response_dict = json.loads(zmq_response)
        action_response = zmq_response_dict.get("action_response")
        action_msg = zmq_response_dict.get("action_msg")
        action_log = zmq_response_dict.get("action_log")

        socket.close()
        context.term()

        return action_response, action_msg, action_log
