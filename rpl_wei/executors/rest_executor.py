"""Handling execution for steps in the RPL-SDL efforts"""
from rpl_wei.core.data_classes import Module, Step, StepStatus
import requests
def wei_rest_callback(step: Step, **kwargs):
    module: Module = kwargs["step_module"]
    base_url = module.config["url"]
    url = base_url + step.args["endpoint"]
    with open(module.config["auth"]) as f:
        headers = {
    "accept": "application/json",
    "Authorization": f.read().strip(),
    "Accept-Language": "en_US"
        }
    payload = {}
    if "payload" in step.args:
        payload = step.args["payload"]
    if step.args["type"] == "Post":
        rest_response = requests.post(url, headers=headers, json=payload)
    elif step.args["type"] == "Get":
        rest_response = requests.get(url, headers=headers)
    elif step.args["type"] == "Put":
        rest_response = requests.put(url, headers=headers, json=payload)
    action_response = rest_response.ok
    action_msg = rest_response.content
    action_log = rest_response.text
    #TODO: assert all of the above. deal with edge cases?
    return action_response, action_msg, action_log