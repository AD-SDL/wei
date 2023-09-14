"""Handling REST execution for steps in the RPL-SDL efforts"""
import json

import requests

from wei.core.data_classes import Interface, Module, Step


class RestInterface(Interface):
    def __init__(self):
        pass

    def send_action(step: Step, **kwargs):
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

    def get_about(config):
        url = config["rest_node_address"]
        rest_response = requests.get(
            url + "/about",
        ).json()
        return rest_response

    def get_state(config):
        url = config["rest_node_address"]
        rest_response = requests.get(
            url + "/state",
        ).json()
        return rest_response

    def get_resources(config):
        url = config["rest_node_address"]
        rest_response = requests.get(
            url + "/resources",
        ).json()
        return rest_response


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
