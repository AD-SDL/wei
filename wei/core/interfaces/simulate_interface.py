"""Handling simulated execution for steps in the RPL-SDL efforts"""
from wei.core.data_classes import Interface, Step


def silent_callback(step: Step, **kwargs):
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
    return "silent", step.action, ""


class SimulateInterface(Interface):
    """A simulated interface for testing WEI workflows"""

    def __init__(self):
        """Initializes the simulated interface"""
        pass

    def send_action(step: Step, **kwargs):
        """Pretends to execute a single step from a workflow, really just prints the step"""
        return silent_callback(step, **kwargs)
