"""A module for utility and helper actions that are broadly useful in different workcells and applications."""

import datetime
import traceback
from typing import Optional

import pause
from fastapi.datastructures import State

from wei.modules.rest_module import RESTModule
from wei.types.step_types import StepSucceeded

utility_module = RESTModule(
    name="utility_module",
    description=__doc__,
    model="WEI Utility Module",
    port=8001,
)


def utility_exception_handler(
    state: State, exception: Exception, error_message: Optional[str] = None
):
    """This function is called whenever a module encounters or throws an irrecoverable exception.
    It should handle the exception (print errors, do any logging, etc.) and set the module status to ERROR."""
    if error_message:
        print(f"Error: {error_message}")
    traceback.print_exc()
    state.error = str(exception)


utility_module.exception_handler = utility_exception_handler


@utility_module.action(blocking=False)
def delay(seconds: float):
    """Set a timer for a specified number of seconds, returning successfully after the timer has elapsed."""
    pause.seconds(seconds)
    return StepSucceeded()


@utility_module.action(blocking=False)
def delay_until(target: datetime.datetime):
    """Blocks until a specific datetime, then returns success."""
    pause.until(datetime.datetime(target))
    return StepSucceeded()


if __name__ == "__main__":
    utility_module.start()
