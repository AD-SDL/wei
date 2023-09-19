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
    def __init__(self):
        pass

    def send_action(step: Step, **kwargs):
        return silent_callback(step, **kwargs)
