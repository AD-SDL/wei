"""Handling execution for steps in the RPL-SDL efforts"""
from typing import Callable, List, Optional

from rpl_wei.data_classes import Module, Step, StepStatus


class StepExecutor:
    """Class to handle executing steps"""

    def __init__(self, run_logger) -> None:
        """Initialize the StepExecutor with necesary tools/data

        Parameters
        ----------
        run_logger : logging.Logger
            The run logger for this run
        """
        self.run_logger = run_logger

    def execute_step(
        self,
        step: Step,
        step_module: Module,
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
        self.run_logger.info(f"Started running step with name: {step.name}")
        self.run_logger.debug(step)

        # The `execution` is really just a callback system.
        # TODO: make a cleaner execution system, less boilerplate for user
        if callbacks:
            for callback in callbacks:
                callback(step, step_module=step_module)

        self.run_logger.info(f"Finished running step with name: {step.name}")

        return StepStatus.SUCCEEDED
