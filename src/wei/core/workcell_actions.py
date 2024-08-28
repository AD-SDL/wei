"""Actions that can be performed on a workcell."""

import datetime
import inspect
import sys
from typing import get_type_hints

import pause

from wei.types.module_types import ModuleAction, ModuleActionArg, ModuleActionFile
from wei.types.step_types import StepSucceeded
from wei.utils import pretty_type_repr


class WorkcellActions:
    """Wrapper for the Workcell actions"""

    actions = []

    @classmethod
    def action(cls, **kwargs):
        """Add an action to the workcell actions."""

        def decorator(function):
            if not kwargs.get("name"):
                kwargs["name"] = function.__name__
            if not kwargs.get("description"):
                kwargs["description"] = function.__doc__
            action = ModuleAction(function=function, **kwargs)
            signature = inspect.signature(function)
            if signature.parameters:
                for parameter_name, parameter_type in get_type_hints(
                    function, include_extras=True
                ).items():
                    if (
                        parameter_name not in action.args
                        and parameter_name not in [file.name for file in action.files]
                        and parameter_name != "state"
                        and parameter_name != "action"
                        and parameter_name != "return"
                    ):
                        if sys.version_info >= (3, 9):
                            type_hint = parameter_type
                        else:
                            type_hint = type(parameter_type)
                        description = ""
                        # * If the type hint is an Annotated type, extract the type and description
                        # * Description here means the first string metadata in the Annotated type
                        if type_hint.__name__ == "Annotated":
                            type_hint = get_type_hints(function, include_extras=False)[
                                parameter_name
                            ]
                            description = next(
                                (
                                    metadata
                                    for metadata in parameter_type.__metadata__
                                    if isinstance(metadata, str)
                                ),
                                "",
                            )
                        if type_hint.__name__ == "UploadFile":
                            # * Add a file parameter to the action
                            action.files.append(
                                ModuleActionFile(
                                    name=parameter_name,
                                    required=True,
                                    description=description,
                                )
                            )
                        else:
                            parameter_info = signature.parameters[parameter_name]
                            # * Add an arg to the action
                            default = (
                                None
                                if parameter_info.default == inspect.Parameter.empty
                                else parameter_info.default
                            )

                            action.args.append(
                                ModuleActionArg(
                                    name=parameter_name,
                                    type=pretty_type_repr(type_hint),
                                    default=default,
                                    required=True if default is None else False,
                                    description=description,
                                )
                            )
            if cls.actions is None:
                cls.actions = []
            cls.actions.append(action)
            return function

        return decorator


@WorkcellActions.action()
def delay(seconds: float):
    """Set a timer for a specified number of seconds, returning successfully after the timer has elapsed."""
    pause.seconds(seconds)
    return StepSucceeded()


@WorkcellActions.action()
def delay_until(target: datetime.datetime):
    """Blocks until a specific datetime, then returns success."""
    pause.until(target)
    return StepSucceeded()
