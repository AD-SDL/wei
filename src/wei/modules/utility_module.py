"""A module for utility and helper actions that are broadly useful in different workcells and applications."""

import datetime

import pause

from wei.modules.rest_module import RESTModule
from wei.types.step_types import StepSucceeded

utility_module = RESTModule(
    name="utility_module",
    description=__doc__,
    model="WEI Utility Module",
    port=8001,
)


@utility_module.action(blocking=False)
def delay(seconds: float):
    """Set a timer for a specified number of seconds, returning successfully after the timer has elapsed."""
    pause.seconds(seconds)
    return StepSucceeded()


@utility_module.action(blocking=False)
def delay_until(target: datetime.datetime):
    """Blocks until a specific datetime, then returns success."""
    pause.until(target)
    return StepSucceeded()


if __name__ == "__main__":
    utility_module.start()
