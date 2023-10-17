"""Handling REST execution for steps in the RPL-SDL efforts"""
import json
from typing import Tuple

import requests

from wei.core.data_classes import Interface, Module, Step


class RestInterface(Interface):
    """Basic Interface for interacting with WEI modules using REST"""

    def __init__(self) -> None:
        """Initializes the REST interface"""
        pass

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
        module: Module = kwargs["step_module"]
        base_url = module.config["rest_node_address"]
        url = base_url + "/action"  # step.args["endpoint"]
        headers = {}

        rest_response = requests.post(
            url,
            headers=headers,
            params={"action_handle": step.action, "action_vars": json.dumps(step.args)},
        ).json()
        action_response = rest_response["action_response"]
        action_msg = rest_response["action_msg"]
        action_log = rest_response["action_log"]

        return action_response, action_msg, action_log

    def get_about(config: dict) -> requests.Response:
        """Gets the about information from the node"""
        url = config["rest_node_address"]
        rest_response = requests.get(
            url + "/about",
        ).json()
        return rest_response

    def get_state(config: dict) -> requests.Response:
        """Gets the state information from the node"""
        url = config["rest_node_address"]
        rest_response = requests.get(
            url + "/state",
        ).json()
        return rest_response

    def get_resources(config: dict) -> requests.Response:
        """Gets the resources information from the node"""
        url = config["rest_node_address"]
        rest_response = requests.get(
            url + "/resources",
        ).json()
        return rest_response
