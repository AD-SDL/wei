"""Handling execution for steps in the RPL-SDL efforts"""
import logging
from typing import Callable, List, Optional

from rpl_wei.core.data_classes import Module, Step, StepStatus

from rpl_wei.core.executors.ros2_executor import wei_ros2_service_callback, wei_ros2_camera_callback
from rpl_wei.core.executors.tcp_executor import wei_tcp_callback


def silent_callback(step: Step, **kwargs):
    print(step)
    return 'silent'

### Executor mapping ###
class Executor_Map:
    function = {
        "wei_ros_node": wei_ros2_service_callback,
        "wei_ros_camera": wei_ros2_camera_callback,
        "wei_tcp_node": wei_tcp_callback,
        "silent_callback": silent_callback,
    }

silent=False
class StepExecutor:
    """Class to handle executing steps"""

    def execute_step(
        self,
        step: Step,
        step_module: Module,
        logger: Optional[logging.Logger] = None,
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
        if silent:
            step_response = Executor_Map.function["silent_callback"](step, step_module=step_module)
        else:
            step_response = Executor_Map.function[step_module.type](step, step_module=step_module)

        logger.info(f"Finished running step with name: {step.name}")

        return step_response, StepStatus.SUCCEEDED
