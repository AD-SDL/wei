"""Handling execution for steps in the RPL-SDL efforts"""
import logging
from typing import Optional

from wei.core.data_classes import Module, Step, StepStatus
from wei.core.interface import Interface_Map


class StepExecutor:
    """Class to handle executing steps"""

    def execute_step(
        self,
        step: Step,
        step_module: Module,
        logger: Optional[logging.Logger] = None,
        simulate: bool = False,
        **kwargs,
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
            ].send_action(step, step_module=step_module)
        else:
            action_response, action_msg, action_log = Interface_Map.function[
                step_module.interface
            ].send_action(step, step_module=step_module)

        logger.info(f"Finished running step with name: {step.name}")

        if not action_response:
            action_response = StepStatus.SUCCEEDED

        return action_response, action_msg, action_log
