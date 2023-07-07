"""Handling execution for steps in the RPL-SDL efforts"""
import requests
import json
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
    url = base_url +  "/action"#step.args["endpoint"]
    headers = {}
    
    # with open(module.config["auth"]) as f:
    #     headers = {
    #         "accept": "application/json",
    #         "Authorization": f.read().strip(),
    #         "Accept-Language": "en_US",
    #     }
    payload = {}
    if "payload" in step.args:
       payload = step.args["payload"]
    rest_response = requests.post(url, headers=headers, params={"action_handle": step.command, "action_vars": json.dumps(step.args)}).json()
    action_response = rest_response["action_response"]
    action_msg = rest_response["action_msg"]
    action_log = rest_response["action_log"]
    # TODO: assert all of the above. deal with edge cases?
    return action_response, action_msg, action_log
