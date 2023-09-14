"""Handling execution for steps in the RPL-SDL efforts"""
import logging
from typing import Optional

from wei.core.data_classes import Module, Step, StepStatus
<<<<<<< HEAD
from wei.core.interfaces.rest_interface import RestInterface
from wei.core.interfaces.ros2_interface import ROS2Interface, wei_ros2_camera_callback
from wei.core.interfaces.simulate_interface import silent_callback
from wei.core.interfaces.tcp_interface import TcpInterface
from wei.core.interfaces.zmq_interface import ZMQInterface
=======
from wei.core.interface import Interface_Map
>>>>>>> 463c9ad49e4f7bfd92d232746715f95674d581f9

########################
#   Executor mapping   #
########################


<<<<<<< HEAD
class Executor_Map:
    """Mapping of YAML names to functions from interfaces"""

    function = {
        "wei_ros_node": ROS2Interface,
        "wei_ros_camera": wei_ros2_camera_callback,
        "wei_tcp_node": TcpInterface,
        "wei_rest_node": RestInterface,
        "wei_zmq_node": ZMQInterface,
        "simulate_callback": silent_callback,
    }


=======
>>>>>>> 463c9ad49e4f7bfd92d232746715f95674d581f9
class StepExecutor:
    """Class to handle executing steps"""

    def execute_step(
        self,
        step: Step,
        step_module: Module,
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
            step_module.interface in Interface_Map.function
        ), f"Executor not found for {step_module.interface}"

        logger.info(f"Started running step with name: {step.name}")
        logger.debug(step)

        # map the correct executor function to the step_module
        if simulate:
            action_response, action_msg, action_log = Interface_Map.function[
                "simulate_callback"
            ](step, step_module=step_module)
        else:
            action_response, action_msg, action_log = Interface_Map.function[
                step_module.interface
            ].send_action(step, step_module=step_module)

        logger.info(f"Finished running step with name: {step.name}")

        if not action_response:
            action_response = StepStatus.SUCCEEDED

        return action_response, action_msg, action_log
