from rpl_wei.core.data_classes import Step


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
