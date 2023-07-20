"""Handling execution for steps in the RPL-SDL efforts"""
import logging
from typing import Callable, List, Optional

from rpl_wei.core.data_classes import Module, Step, StepStatus
from rpl_wei.core.interfaces.rest_interface import wei_rest_callback
from rpl_wei.core.interfaces.ros2_interface import (
    wei_ros2_camera_callback,
    wei_ros2_service_callback,
)
from rpl_wei.core.interfaces.simulate_interface import silent_callback
from rpl_wei.core.interfaces.tcp_interface import wei_tcp_callback
from rpl_wei.core.interfaces.zmq_interface import wei_zmq_callback

########################
#   Executor mapping   #
########################


class Executor_Map:
    function = {
        "wei_ros_node": wei_ros2_service_callback,
        "wei_ros_camera": wei_ros2_camera_callback,
        "wei_tcp_node": wei_tcp_callback,
        "wei_rest_node": wei_rest_callback,
        "wei_zmq_node": wei_zmq_callback,
        "simulate_callback": silent_callback,
    }


class StepExecutor:
    """Class to handle executing steps"""

    def execute_step(
        self,
        step: Step,
        step_module: Module,
        locations: Optional[dict] = None,
        callbacks: Optional[List[Callable]] = None,
        logger: Optional[logging.Logger] = None,
        simulate: bool = False,
    ) -> StepStatus:
        """Executes a single step from a workflow without making any message calls

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
        assert (
            step_module.interface in Executor_Map.function
        ), f"Executor not found for {step_module.interface}"

        logger.info(f"Started running step with name: {step.name}")
        logger.debug(step)

        # map the correct executor function to the step_module
        if simulate:
            action_response, action_msg, action_log = Executor_Map.function[
                "simulate_callback"
            ](step, step_module=step_module)
        else:
            action_response, action_msg, action_log = Executor_Map.function[
                step_module.interface
            ](step, step_module=step_module)

        logger.info(f"Finished running step with name: {step.name}")

        if not action_response:
            action_response = StepStatus.SUCCEEDED

        return action_response, action_msg, action_log
