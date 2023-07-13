"""Handling execution for steps in the RPL-SDL efforts"""
import json

import requests

from rpl_wei.core.data_classes import Module, Step


def wei_rest_callback(step: Step, **kwargs):
    """Executes a single step from a workflow using a REST messaging framework

    Parameters
    ----------
    step : Step
        A single step from a workflow definition

    Returns
    -------
    action_response: StepStatus
        A status of the step (in theory provides async support with IDLE, RUNNING, but for now is just SUCCEEDED/FAILED)
    action_msg: str
        the data or informtaion returned from running the step.
    action_log: str
        A record of the exeution of the step

    """
    module: Module = kwargs["step_module"]
    base_url = module.config["url"]
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
