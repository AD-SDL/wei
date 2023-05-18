"""Handling execution for steps in the RPL-SDL efforts"""
from rpl_wei.core.data_classes import Module, Step

def wei_tcp_callback(step: Step, **kwargs):
    from socket import socket

    module: Module = kwargs["step_module"]

    sock = socket.bind(module.config["tcp_address"], module.config["tcp_port"])
    msg = {
        "action_handle": step.command,
        "action_vars": step.args,
    }

    socket.send(str(msg).encode())
    answer = socket.read().decode()
    answer = eval(answer)
    #TODO: assert dict
    return answer
