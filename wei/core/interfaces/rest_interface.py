"""Handling REST execution for steps in the RPL-SDL efforts"""

import json
from pathlib import Path
from typing import Any, Dict, Tuple

import requests

from wei.core.data_classes import Interface, Module, Step, StepResponse, StepStatus


class RestInterface(Interface):
    """Basic Interface for interacting with WEI modules using REST"""

    def __init__(self) -> None:
        """Initializes the REST interface"""
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
        for key in ["rest_node_address"]:
            if key not in config:
                return False
        return True

    @staticmethod
    def send_action(
        step: Step, module: Module, **kwargs: Any
    ) -> Tuple[StepStatus, str, str]:
        """Executes a single step from a workflow using a REST API

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
        base_url = module.config["rest_node_address"]
        url = base_url + "/action"  # step.args["endpoint"]

        rest_response = requests.post(
            url,
            params={"action_handle": step.action, "action_vars": json.dumps(step.args)},
            files=[
                ("files", (file, open(path, "rb"))) for file, path in step.files.items()
            ],
        )
        try:
            print(rest_response.status_code)
            print(rest_response.json())
        except Exception as _:
            pass
        if "x-wei-action_response" in rest_response.headers:
            response = StepResponse.from_headers(dict(rest_response.headers))
            if "run_dir" in kwargs.keys():
                path = Path(
                    kwargs["run_dir"],
                    "results",
                    Path(step.id + "_" + Path(response.action_msg).name),
                )
                path.parent.mkdir(parents=True, exist_ok=True)
            else:
                path = Path(step.id + "_" + Path(response.action_msg).name)
            with open(str(path), "wb") as f:
                f.write(rest_response.content)
            response.action_msg = path.name
        else:
            response = StepResponse.model_validate(rest_response.json())
        action_response = response.action_response
        action_msg = response.action_msg
        action_log = response.action_log

        return action_response, action_msg, action_log

    @staticmethod
    def get_about(module: Module, **kwargs: Any) -> Any:
        """Gets the about information from the node"""
        url = module.config["rest_node_address"]
        rest_response = requests.get(
            url + "/about",
            timeout=10,
        ).json()
        return rest_response

    @staticmethod
    def get_state(module: Module, **kwargs: Any) -> Any:
        """Gets the state information from the node"""
        url = module.config["rest_node_address"]
        rest_response = requests.get(
            url + "/state",
            timeout=10,
        ).json()
        return rest_response

    @staticmethod
    def get_resources(module: Module, **kwargs: Any) -> Any:
        """Gets the resources information from the node"""
        url = module.config["rest_node_address"]
        rest_response = requests.get(
            url + "/resources",
            timeout=10,
        ).json()
        return dict(rest_response)

    @staticmethod
    def send_admin_command(module: Module, command: str, **kwargs: Any) -> Any:
        """Sends a command to the node"""
        url = module.config["rest_node_address"]
        rest_response = requests.post(
            url + "/admin/" + command,
            timeout=10,
        ).json()
        return rest_response
