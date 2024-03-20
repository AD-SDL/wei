"""Handling simulated execution for steps in the RPL-SDL efforts"""

from typing import Any, Dict, Tuple

from wei.core.data_classes import Interface, Module, ModuleStatus, Step, StepStatus


def silent_callback(step: Step, **kwargs: Any) -> Tuple[str, str, str]:
    """prints a single step from a workflow using no messaging framework

    Parameters
    ----------
    step : Step
        A single step from a workflow definition

    Returns
    -------
    response: str
    A dummy string

    """
    print(step)
    return StepStatus.SUCCEEDED, step.action, ""


class SimulateInterface(Interface):
    """A simulated interface for testing WEI workflows"""

    @staticmethod
    def config_validator(config: Dict[str, Any]) -> bool:
        """Validates the configuration for the interface"""
        return True

    @staticmethod
    def send_action(step: Step, module: Module, **kwargs: Any) -> Tuple[str, str, str]:
        """Pretends to execute a single step from a workflow, really just prints the step"""
        return silent_callback(step, **kwargs)

    @staticmethod
    def get_state(module: Module, **kwargs: Any) -> Dict[str, Any]:
        """Returns the current state of the module"""
        return {"State": ModuleStatus.IDLE}
