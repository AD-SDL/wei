"""Handling execution for steps in the RPL-SDL efforts"""
import json
from typing import Any, Tuple

from wei.core.data_classes import Interface, Module, Step


class TcpInterface(Interface):
    """Basic Interface for interacting with WEI modules using TCP"""

    def __init__(self) -> None:
        """Initializes the TCP interface"""
        pass

    @staticmethod
    def config_validator(config: dict[str, Any]) -> bool:
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
        for key in ["tcp_node_address", "tcp_node_port"]:
            if key not in config:
                return False
        return True

    def send_action(step: Step, **kwargs) -> Tuple[str, str, str]:
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
        import socket

        module: Module = kwargs["step_module"]
        sock = socket.socket()
        sock.connect(
            (module.config["tcp_node_address"], int(module.config["tcp_node_port"]))
        )
        msg = {
            "action_handle": step.action,
            "action_vars": step.args,
        }
        msg = json.dumps(msg)
        sock.send(msg.encode())
        # TODO: add continuous monitoring on the response?
        tcp_response = sock.recv(1024).decode()
        tcp_response = json.loads(tcp_response)
        action_response = tcp_response.get("action_response")
        action_msg = tcp_response.get("action_msg")
        action_log = tcp_response.get("action_log")
        # TODO: assert all of the above. deal with edge cases?
        sock.close()
        return action_response, action_msg, action_log
