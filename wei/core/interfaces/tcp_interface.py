"""Handling execution for steps in the RPL-SDL efforts"""

import json
from typing import Any, Dict, Tuple

from wei.core.data_classes import Interface, Module, Step

try:
    import socket  # type: ignore
except ImportError:
    print("Socket not found. Cannot use TCPInterface")


class TcpInterface(Interface):
    """Basic Interface for interacting with WEI modules using TCP"""

    def __init__(self) -> None:
        """Initializes the TCP interface"""
        pass

    @staticmethod
    def config_validator(config: Dict[str, Any]) -> bool:
        """Validates the configuration for the interface

        Parameters
        ----------
        config : Dict
            The configuration for the module

        Returns
        -------
        bool
            Whether the configuration is valid or not
        """
        for key in ["tcp_node_address", "tcp_node_port"]:
            if key not in config:
                return False
        return True

    @staticmethod
    def send_action(step: Step, module: Module, **kwargs: Any) -> Tuple[str, str, str]:
        """Executes a single step from a workflow using a TCP messaging framework

        Parameters
        ----------
        step : Step
            A single step from a workflow definition

        Returns
        -------
        action_response: str
            A status of the step (in theory provides async support with IDLE, RUNNING, but for now is just SUCCEEDED/FAILED)
        action_msg: str
            the data or information returned from running the step.
        action_log: str
            A record of the execution of the step

        """

        sock = socket.socket()
        sock.connect(
            (module.config["tcp_node_address"], int(module.config["tcp_node_port"]))
        )
        msg = {
            "action_handle": step.action,
            "action_vars": step.args,
        }
        sock.send(json.dumps(msg).encode())
        tcp_response = sock.recv(1024).decode()
        tcp_response_dict = json.loads(tcp_response)
        action_response = tcp_response_dict.get("action_response")
        action_msg = tcp_response_dict.get("action_msg")
        action_log = tcp_response_dict.get("action_log")
        sock.close()
        return action_response, action_msg, action_log
