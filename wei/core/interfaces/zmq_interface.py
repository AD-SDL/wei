"""Handling ZMQ execution for steps in the RPL-SDL efforts"""
import json

import zmq

from wei.core.data_classes import Interface, Module, Step


class ZMQInterface(Interface):
    def __init__(self):
        pass

    def send_action(step: Step, **kwargs):
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
            the data or informtaion returned from running the step.
        action_log: str
            A record of the exeution of the step

        """
        module: Module = kwargs["step_module"]
        context = zmq.Context()
        socket = context.socket(zmq.REQ)
        socket.connect(
            f"tcp://{module.config['zmq_node_address']}:{module.config['zmq_node_port']}"
        )

        msg = {
            "action_handle": step.action,
            "action_vars": step.args,
        }
        msg = json.dumps(msg)
        socket.send_string(msg)
        zmq_response = (
            socket.recv().decode()
        )  # does this need to be decoded with "utf-8"?
        zmq_response = json.loads(zmq_response)
        action_response = zmq_response.get("action_response")
        action_msg = zmq_response.get("action_msg")
        action_log = zmq_response.get("action_log")

        socket.close()
        context.term()

        # TODO: assert all of the above. Deal with edge cases?

        return action_response, action_msg, action_log

    def get_about(config):
        return {}

    def get_state(config):
        return {}

    def get_resources(config):
        return {}
