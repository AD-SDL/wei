from rpl_wei.core.data_classes import Step


def silent_callback(step: Step, **kwargs):
    print(step)
    return "silent", step.action, ""
