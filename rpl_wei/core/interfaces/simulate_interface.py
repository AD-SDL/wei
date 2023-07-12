import requests

from rpl_wei.core.data_classes import Module, Step, Interface


def silent_callback(step: Step, **kwargs):
    print(step)
    return "silent", step.action, ""
