"""Handling simulated execution for steps in the RPL-SDL efforts"""
from wei.core.data_classes import Step
from wei.core.data_classes import Interface


class SimulateInterface(Interface):
    def __init__(self):
        pass


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
