"""Handling execution for steps in the RPL-SDL efforts"""
from rpl_wei.core.data_classes import Module, Step
import json


def wei_tcp_callback(step: Step, **kwargs):
    """Executes a single step from a workflow using a TCP messaging framework

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
    import socket

    module: Module = kwargs["step_module"]
    sock = socket.socket()
    sock.connect((module.config["tcp_address"], int(module.config["tcp_port"])))
    msg = {
        "action_handle": step.command,
        "action_vars": step.args,
    }
    msg = json.dumps(msg)
    sock.send(msg.encode())
    # TODO: add continuous monitoring on the response?
    tcp_response = sock.recv(1024).decode()
    tcp_response = json.loads(tcp_response)
    print(tcp_response)
    action_response = tcp_response.get("action_response")
    action_msg = tcp_response.get("action_msg")
    action_log = tcp_response.get("action_log")
    # TODO: assert all of the above. deal with edge cases?
    sock.close()
    return action_response, action_msg, action_log
