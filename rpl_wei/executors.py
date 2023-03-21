"""Handling execution for steps in the RPL-SDL efforts"""
import logging
from typing import Callable, List, Optional

from rpl_wei.data_classes import Module, Step, StepStatus

try:
    import rclpy
except ImportError:
    print("No RCLPY found... Cannot use ROS")
    rclpy = None

wei_execution_node = None


def __init_rclpy():
    global wei_execution_node
    from wei_executor.weiExecutorNode import weiExecNode

    if not rclpy.utilities.ok():
        rclpy.init()
        print("Started RCLPY")
        wei_execution_node = weiExecNode()
    else:
        print("RCLPY OK ")


def __kill_node():
    global wei_execution_node
    print("killing node")
    wei_execution_node.destroy_node()
    rclpy.shutdown()


# Callbacks
def wei_service_callback(step: Step, **kwargs):
    __init_rclpy()

    module: Module = kwargs["step_module"]

    msg = {
        "node": module.config["ros_node"],
        "action_handle": step.command,
        "action_vars": step.args,
    }

    if kwargs.get("verbose", False):
        print("\n Callback message:")
        print(msg)
        print()

    res = wei_execution_node.send_wei_command(
        msg["node"], msg["action_handle"], msg["action_vars"]
    )
    if res:
        print(res)

    __kill_node()


def wei_camera_callback(step: Step, **kwargs):
    __init_rclpy()
    module: Module = kwargs["step_module"]

    wei_execution_node.capture_image(
        node_name=module.config["ros_node"],
        image_name=step.args["file_name"],
        path=step.args["save_location"],
    )
    __kill_node()

def wei_tcp_callback(step: Step, **kwargs):
    from socket import socket
    module: Module = kwargs["step_module"]

    sock = socket.bind(module.config["tcp_address"],module.config["tcp_port"])
    msg = {
        "action_handle": step.command,
        "action_vars": step.args,
    }

    socket.send(str(msg).encode())
    answer = socket.read().decode()
    return 

def silent_callback(step: Step, **kwargs):
    print(step)


### Executor mapping ###
class Executor_Map:
    function = {
        "wei_ros_node": wei_service_callback,
        "wei_ros_camera": wei_camera_callback,
        "wei_tcp_node": wei_tcp_callback,
        "silent_callback": silent_callback,
    }


class StepExecutor:
    """Class to handle executing steps"""

    def execute_step(
        self,
        step: Step,
        step_module: Module,
        logger: Optional[logging.Logger] = None,
        callbacks: Optional[List[Callable]] = None,
    ) -> StepStatus:
        """Executes a single step from a workflow

        Parameters
        ----------
        step : Step
            A single step from a workflow definition

        Returns
        -------
        StepStatus
            A status of the step (in theory provides async support with IDLE, RUNNING, but for now is just SUCCEEDED/FAILED)
        """
        assert (
            step_module.type in Executor_Map.function
        ), f"Executor not found for {step_module.type}"

        logger.info(f"Started running step with name: {step.name}")
        logger.debug(step)

        # map the correct executor function to the step_module
        if rclpy is not None:
            Executor_Map.function[step_module.type](step, step_module=step_module)
        else:
            Executor_Map.function["silent_callback"](step, step_module=step_module)

        # TODO: Allow for callbacks, disabled for now because we are switching to the in-package callbacks
        # if callbacks:
        #     for callback in callbacks:
        #         callback(step, step_module=step_module)

        logger.info(f"Finished running step with name: {step.name}")

        return StepStatus.SUCCEEDED
