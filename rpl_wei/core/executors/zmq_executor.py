import zmq

from rpl_wei.core.data_classes import Module, Step


def wei_zmq_callback(step: Step, **kwargs):
   """Executes a single step from a workflow using a TCP messaging framework with the ZMQ library

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
    socket.connect(f"tcp://{module.config['tcp_address']}:{module.config['tcp_port']}")

    msg = {
        "action_handle": step.command,
        "action_vars": step.args,
    }

    socket.send(str(msg))
    zmq_response = socket.recv().decode()  # does this need to be decoded with "utf-8"?
    zmq_response = eval(zmq_response)
    print(zmq_response)

    action_response = eval(zmq_response.get("action_response"))
    action_msg = zmq_response.get("action_msg")
    action_log = zmq_response.get("action_log")

    socket.close()
    context.term()

    # TODO: assert all of the above. Deal with edge cases?

    return action_response, action_msg, action_log
