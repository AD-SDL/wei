"""REST Module Convenience Class"""

import argparse
import importlib.metadata
import inspect
import os
import signal
import sys
import time
import traceback
import warnings
from contextlib import asynccontextmanager
from threading import Lock, Thread
from typing import Any, List, Optional, Set, Union

from fastapi import (
    APIRouter,
    BackgroundTasks,
    FastAPI,
    Request,
    Response,
    UploadFile,
    status,
)
from fastapi.datastructures import State
from typing_extensions import Annotated, get_type_hints

from wei.types import ModuleStatus
from wei.types.module_types import (
    AdminCommands,
    ModuleAbout,
    ModuleAction,
    ModuleActionArg,
    ModuleActionFile,
    ModuleState,
)
from wei.types.step_types import (
    ActionRequest,
    StepFileResponse,
    StepResponse,
    StepStatus,
)
from wei.utils import pretty_type_repr


class RESTModule:
    """A convenience class for creating REST-powered WEI modules."""

    name: Optional[str] = None
    """A unique name for this particular instance of this module.
    This is required, and should generally be set by the command line."""
    arg_parser: Optional[argparse.ArgumentParser] = None
    """An argparse.ArgumentParser object that can be used to parse command line arguments. If not set in the constructor, a default will be used."""
    about: Optional[ModuleAbout] = None
    """A ModuleAbout object that describes the module.
    This is used to provide information about the module to user's and WEI.
    Will be generated from attributes if not set."""
    description: str = ""
    """A description of the module and the devices/resources it controls."""
    status: ModuleStatus = ModuleStatus.INIT
    """The current status of the module."""
    error: Optional[str] = None
    """Any error message that has occurred during the module's operation."""
    model: Optional[str] = None
    """The model of instrument or resource this module manages."""
    interface: str = "wei_rest_node"
    """The interface used by the module."""
    actions: List[ModuleAction] = []
    """A list of actions that the module can perform."""
    resource_pools: List[Any] = []
    """A list of resource pools used by the module."""
    admin_commands: Set[AdminCommands] = set()
    """A list of admin commands supported by the module."""
    wei_version: Optional[str] = importlib.metadata.version("ad_sdl.wei")
    """The version of WEI that this module is compatible with."""
    pre_locked_status = ModuleStatus.INIT
    """The status of the module before it was locked"""
    pre_paused_status = ModuleStatus.INIT
    """The status of the module before it was paused"""

    _actions_running = 0
    """Keep track of how many actions are currently running"""

    def __init__(
        self,
        arg_parser: Optional[argparse.ArgumentParser] = None,
        description: str = "",
        model: Optional[str] = None,
        interface: str = "wei_rest_node",
        actions: Optional[List[ModuleAction]] = None,
        resource_pools: Optional[List[Any]] = None,
        admin_commands: Optional[Set[AdminCommands]] = None,
        name: Optional[str] = None,
        host: Optional[str] = "0.0.0.0",
        port: Optional[int] = 2000,
        about: Optional[ModuleAbout] = None,
        **kwargs,
    ):
        """Creates an instance of the RESTModule class"""
        self.app = FastAPI(lifespan=RESTModule._lifespan, description=description)
        self.app.state = State(state={})
        self.state = self.app.state  # * Mirror the state object for easier access
        self.state.action_lock = Lock()
        self.router = APIRouter()

        # * Set attributes from constructor arguments
        self.name = name
        self.about = about
        self.host = host
        self.port = port
        self.description = description
        self.model = model
        self.interface = interface
        self.actions = actions if actions else []
        self.resource_pools = resource_pools if resource_pools else []
        self.admin_commands = (
            admin_commands
            if admin_commands
            else set(
                [
                    AdminCommands.SHUTDOWN,
                    AdminCommands.RESET,
                    AdminCommands.LOCK,
                    AdminCommands.UNLOCK,
                ]
            )
        )

        # * Set any additional keyword arguments as attributes as well
        # * These will then get added to the state object
        for key, value in kwargs.items():
            setattr(self, key, value)

        # * Set up the argument parser
        if arg_parser:
            self.arg_parser = arg_parser
        else:
            self.arg_parser = argparse.ArgumentParser(description=description)
            self.arg_parser.add_argument(
                "--host",
                type=str,
                default=self.host,
                help="Hostname or IP address to bind to (0.0.0.0 for all interfaces)",
            )
            self.arg_parser.add_argument(
                "--port",
                type=int,
                default=self.port,
                help="Hostname or IP address to bind to (0.0.0.0 for all interfaces)",
            )
            self.arg_parser.add_argument(
                "--alias",
                "--name",
                "--node_name",
                type=str,
                default=self.name,
                help="A unique name for this particular instance of this module",
            )

    # * Module and Application Lifecycle Functions

    @staticmethod
    def _startup_handler(state: State):
        """This function is called when the module needs to startup any devices or resources.
        It should be overridden by the developer to do any necessary setup for the module."""
        warnings.warn(
            message="No module-specific startup defined, use the @<class RestModule>.startup decorator or override `_startup_handler` to define.",
            category=UserWarning,
            stacklevel=1,
        )

    def startup(self):
        """Decorator to add a startup_handler to the module"""

        def decorator(function):
            if inspect.isgenerator(function) or inspect.isgeneratorfunction(function):
                raise Exception(
                    "Startup handler cannot be a coroutine. Use a regular function (i.e. make sure you don't have a yield statement)."
                )
            self._startup_handler = function
            return function

        return decorator

    @staticmethod
    def _shutdown_handler(state: State):
        """This function is called when the module needs to teardown any devices or resources.
        It should be overridden by the developer to do any necessary teardown for the module."""
        warnings.warn(
            message="No module-specific shutdown defined, override `_shutdown_handler` to define.",
            category=UserWarning,
            stacklevel=1,
        )

    def shutdown(self):
        """Decorator to add a shutdown_handler to the module"""

        def decorator(function):
            self._shutdown_handler = function
            return function

        return decorator

    @staticmethod
    def exception_handler(
        state: State, exception: Exception, error_message: Optional[str] = None
    ):
        """This function is called whenever a module encounters or throws an irrecoverable exception.
        It should handle the exception (print errors, do any logging, etc.) and set the module status to ERROR."""
        if error_message:
            print(f"Error: {error_message}")
        traceback.print_exc()
        state.status[ModuleStatus.ERROR] = True
        state.status[ModuleStatus.READY] = False
        state.error = str(exception)

    @staticmethod
    def startup_thread(state: State):
        """Runs the startup function for the module in a non-blocking thread, with error handling"""
        try:
            # * Call the module's startup function
            state.status = ModuleState().status
            state._startup_handler(state=state)
        except Exception as exception:
            # * If an exception occurs during startup, handle it and put the module in an error state
            state.exception_handler(state, exception, "Error during startup")
            state.status[ModuleStatus.ERROR] = True
            state.status[ModuleStatus.READY] = (
                False  # * Make extra sure the status is set to ERROR
            )
        else:
            # * If everything goes well, set the module status to IDLE
            if state.status[ModuleStatus.INIT]:
                state.status[ModuleStatus.INIT] = False
                state.status[ModuleStatus.READY] = True
                print(
                    "Startup completed successfully. Module is now ready to accept actions."
                )
            elif state.status[ModuleStatus.ERROR]:
                print("Startup completed with errors.")

    @asynccontextmanager
    @staticmethod
    async def _lifespan(app: FastAPI):
        """Initializes the module, doing any instrument startup and starting the REST app."""

        # * Run startup on a separate thread so it doesn't block the rest server from starting
        # * (module won't accept actions until startup is complete)
        Thread(target=RESTModule.startup_thread, args=[app.state]).start()

        yield

        try:
            # * Call any shutdown logic
            app.state._shutdown_handler(app.state)
        except Exception as exception:
            # * If an exception occurs during shutdown, handle it so we at least see the error in logs/terminal
            app.state.exception_handler(app.state, exception, "Error during shutdown")

    # * Module State Handling Functions

    @staticmethod
    def _state_handler(state: State) -> ModuleState:
        """This function is called when the module is asked for its current state. It should return a dictionary of the module's current state.
        This function can be overridden by the developer to provide more specific state information using the `@<class RestModule>.state_handler` decorator.
        At a minimum, it should return the module's current status, defined as the top-level 'status' key."""
        warnings.warn(
            message="No module-specific state handler defined, use the `@<class RestModule>.state_handler` decorator to define.",
            category=UserWarning,
            stacklevel=1,
        )

        return ModuleState(status=state.status, error=state.error)

    def state_handler(self):
        """Decorator to add custom logic for the published state on the /state endpoint.
        This should return a dictionary of the module's current state that is compliant with the `wei.types.module_types.ModuleState` model."""

        def decorator(function):
            self._state_handler = function
            return function

        return decorator

    # * Module Action Handling Functions

    def action(self, **kwargs):
        """Decorator to add an action to the module.
        This decorator can be used to define actions that the module can perform.

        Args:
            `name: str`
                The name of the action. If not provided, the name of the function will be used.
            `description: str`
                A description of the action. If not provided, the function's docstring will be used.
        """

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
                            parameter_info = signature.parameters[parameter_name]
                            action.files.append(
                                ModuleActionFile(
                                    name=parameter_name,
                                    required=True
                                    if parameter_info.default
                                    == inspect.Parameter.empty
                                    is None
                                    else False,
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
                                    required=True
                                    if parameter_info.default
                                    == inspect.Parameter.empty
                                    is None
                                    else False,
                                    description=description,
                                )
                            )
            if self.actions is None:
                self.actions = []
            self.actions.append(action)
            return function

        return decorator

    @staticmethod
    def action_handler(
        state: State, action: ActionRequest
    ) -> Union[StepResponse, StepFileResponse]:
        """This function is called whenever an action is requested from the module.
        It should return a StepResponse object that indicates the success or failure of the action.
        Note: If overridden, this function should handle all actions for the module (i.e. any actions defined using the decorator should also be handled here).
        """
        if not state.actions:
            warnings.warn(
                message="No actions or module-specific action handler defined, override `action_handler` or set `state.actions`.",
                category=UserWarning,
                stacklevel=1,
            )
            return StepResponse.step_failed(
                error=f"action: {action.name}, args: {action.args}",
            )
        else:
            for module_action in state.actions:
                if module_action.name == action.name:
                    if not module_action.function:
                        return StepResponse.step_failed(
                            error="Action is defined, but not implemented. Please define a `function` for the action, or use the `@<class RestModule>.action` decorator."
                        )

                    # * Check if the module is ready to accept actions
                    try:
                        state.get_action_lock(
                            state=state, action=action, blocking=module_action.blocking
                        )
                    except Exception:
                        error_message = f"Module is not ready to accept actions. Module Status: {state.status}"
                        print(error_message)
                        return StepResponse.step_not_ready(error=error_message)

                    # * Prepare arguments for the action function.
                    # * If the action function has a 'state' or 'action' parameter
                    # * we'll pass in our state and action objects.
                    arg_dict = {}
                    parameters = inspect.signature(module_action.function).parameters
                    if parameters.__contains__("state"):
                        arg_dict["state"] = state
                    if parameters.__contains__("action"):
                        arg_dict["action"] = action
                    if (
                        list(parameters.values())[-1].kind
                        == inspect.Parameter.VAR_KEYWORD
                    ):
                        # * Function has **kwargs, so we can pass all action args and files
                        arg_dict = {**arg_dict, **action.args}
                        arg_dict = {
                            **arg_dict,
                            **{file.filename: file.file for file in action.files},
                        }
                    else:
                        for arg_name, arg_value in action.args.items():
                            if arg_name in parameters.keys():
                                arg_dict[arg_name] = arg_value
                        for file in action.files:
                            if file.filename in parameters.keys():
                                arg_dict[file.filename] = file

                    for arg in module_action.args:
                        if arg.name not in action.args:
                            if arg.required:
                                return StepResponse.step_failed(
                                    error=f"Missing required argument '{arg.name}'"
                                )
                    for file in module_action.files:
                        if not any(
                            arg_file.filename == file.name for arg_file in action.files
                        ):
                            if file.required:
                                return StepResponse.step_failed(
                                    error=f"Missing required file '{file.name}'"
                                )

                    # * Perform the action here and return result
                    result = module_action.function(**arg_dict)
                    if isinstance(result, StepResponse) or isinstance(
                        result, StepFileResponse
                    ):
                        return result
                    elif result is None:
                        # *Assume success if no return value and no exception
                        return StepResponse.step_succeeded()
                    else:
                        # * Return a failure if the action returns something unexpected
                        return StepResponse.step_failed(
                            error=f"Action '{action.name}' returned an unexpected value: {result}"
                        )
            return StepResponse.step_failed(error=f"Action '{action.name}' not found")

    @staticmethod
    def get_action_lock(state: State, action: ActionRequest, blocking: bool = True):
        """This function is used to ensure the module only performs actions when it is safe to do so.
        In most cases, this means ensuring the instrument is not currently acting
        and then setting the module's status to BUSY to prevent other actions from being taken for the duration.
        This can be overridden by the developer to provide more specific behavior.
        """
        if blocking:
            state.action_lock.acquire()
        if state.status[ModuleStatus.READY] and not (
            state.status[ModuleStatus.PAUSED] or state.status[ModuleStatus.LOCKED]
        ):
            if blocking:
                state.status[ModuleStatus.READY] = False
                state.status[ModuleStatus.RUNNING] = True
            else:
                state.status[ModuleStatus.RUNNING] = True
            state._actions_running += 1
        else:
            state.action_lock.release()
            raise Exception("Module is not ready to accept actions")
        if blocking:
            state.action_lock.release()

    @staticmethod
    def release_action_lock(state: State, action: ActionRequest):
        """Releases the lock on the module. This should be called after an action is completed.
        This can be overridden by the developer to provide more specific behavior.
        """
        with state.action_lock:
            if state._actions_running >= 1:
                state._actions_running -= 1
                if state._actions_running == 0:
                    state.status[ModuleStatus.RUNNING] = False
        if not state.status[ModuleStatus.READY]:
            state.status[ModuleStatus.READY] = True

    # * Admin Command Handling Functions

    @staticmethod
    def _safety_stop(state: State):
        """Handles custom safety-stop functionality"""
        state.status[ModuleStatus.CANCELLED] = True
        state.status[ModuleStatus.LOCKED] = True
        return {"message": "Module safety-stopped"}

    def safety_stop(self):
        """Decorator to add safety_stop functionality to the module"""

        def decorator(function):
            self.admin_commands.add(AdminCommands.SAFETY_STOP)
            self._safety_stop = function
            return function

        return decorator

    def pause(self):
        """Decorator to add pause functionality to the module"""

        def decorator(function):
            self.admin_commands.add(AdminCommands.PAUSE)
            self._pause = function
            return function

        return decorator

    @staticmethod
    def _pause(state: State):
        """Handles pausing the module. This should be overridden by the developer to provide custom behavior."""
        state.pre_paused_status = state.status
        state.status[ModuleStatus.PAUSED] = True
        return {"message": "Module paused"}

    def resume(self):
        """Decorator to add resume functionality to the module"""

        def decorator(function):
            self.admin_commands.add(AdminCommands.RESUME)
            self._resume = function
            return function

        return decorator

    @staticmethod
    def _resume(state: State):
        """Handles resuming the module from the paused state. This should be overridden by the developer to provide custom behavior."""
        if state.status[ModuleStatus.PAUSED]:
            state.status[ModuleStatus.PAUSED] = False
            return {"message": "Module resumed"}
        else:
            return {"message": "Module not paused"}

    def reset(self):
        """Decorator to add reset functionality to the module"""

        def decorator(function):
            self.admin_commands.add(AdminCommands.RESET)
            self._reset = function
            return function

        return decorator

    @staticmethod
    def _reset(state: State):
        """This function is called when the module needs to be reset.
        It should be overridden by the developer to do any necessary teardown for the module."""
        state.status[ModuleStatus.INIT] = True
        state.status[ModuleStatus.READY] = False
        try:
            state._shutdown_handler(state)
            Thread(target=RESTModule.startup_thread, args=[state]).start()
            return {"message": "Module reset"}
        except Exception as e:
            state.exception_handler(
                state, e, "Error while attempting to reset the module"
            )
            return {"error": "Error while attempting to reset the module"}

    def cancel(self):
        """Decorator to add cancellation functionality to the module"""

        def decorator(function):
            self.admin_commands.add(AdminCommands.CANCEL)
            self._cancel = function
            return function

        return decorator

    @staticmethod
    def _cancel(state: State):
        """Handles cancelling any running actions on the module. This should be overridden by the developer to provide custom behavior."""
        state.status[ModuleStatus.CANCELLED] = True
        return {"message": "Module actions canceled"}

    def lock(self):
        """Decorator to add locking functionality to the module"""

        def decorator(function):
            self.admin_commands.add(AdminCommands.LOCK)
            self._lock = function
            return function

        return decorator

    @staticmethod
    def _lock(state: State):
        """Handles locking the module. This should be overridden by the developer to provide custom behavior."""
        state.pre_locked_status = state.status
        state.status[ModuleStatus.LOCKED] = True
        return {"message": "Module paused"}

    def unlock(self):
        """Decorator to add unlocking functionality to the module"""

        def decorator(function):
            self.admin_commands.add(AdminCommands.UNLOCK)
            self._unlock = function
            return function

        return decorator

    @staticmethod
    def _unlock(state: State):
        """Logic for unlocking the module. This should be overridden by the developer to provide custom behavior."""
        if state.status[ModuleStatus.LOCKED]:
            state.status[ModuleStatus.LOCKED] = False
            return {"message": "Module unlocked"}
        else:
            return {"message": "Module not locked"}

    def _configure_routes(self):
        """Configure the API endpoints for the REST module"""

        @self.router.post("/admin/shutdown")
        async def shutdown(background_tasks: BackgroundTasks):
            def shutdown_server():
                time.sleep(1)
                pid = os.getpid()
                os.kill(pid, signal.SIGTERM)

            background_tasks.add_task(shutdown_server)
            return {"message": "Shutting down server"}

        @self.router.post("/admin/{admin_command}")
        async def admin_command_handler(request: Request, admin_command: str):
            state = request.app.state
            if admin_command in self.admin_commands:
                try:
                    return getattr(self, f"_{admin_command.lower()}")(state)
                except AttributeError:
                    return {
                        "message": f"Admin command '{admin_command}' not implemented"
                    }
            else:
                return status.HTTP_404_NOT_FOUND

        @self.router.get("/state")
        async def state(request: Request) -> ModuleState:
            state = request.app.state
            # * If the module is in INIT, return without calling custom state handler
            if state.status in [ModuleStatus.INIT, ModuleStatus.ERROR]:
                return ModuleState(status=state.status, error=state.error)
            return self._state_handler(state=state)

        @self.router.get("/resources")
        async def resources(request: Request):
            # state = request.app.state
            return {"resources": {}}

        @self.router.get("/about")
        async def about(request: Request, response: Response) -> ModuleAbout:
            state = request.app.state
            if state.about:
                return state.about
            else:
                try:
                    state.about = ModuleAbout.model_validate(
                        state, from_attributes=True
                    )
                    return state.about
                except Exception:
                    traceback.print_exc()
                    return {"error": "Unable to generate module about"}

        @self.router.post("/action")
        def action(
            request: Request,
            response: Response,
            action_handle: str,
            action_vars: Optional[str] = None,
            files: List[UploadFile] = [],  # noqa: B006
        ):
            """Handles incoming action requests to the module. Returns a StepResponse or StepFileResponse object."""
            action_request = ActionRequest(
                name=action_handle, args=action_vars, files=files
            )
            state = request.app.state

            # * Try to run the action_handler for this module
            try:
                step_result = state.action_handler(state=state, action=action_request)
                if (
                    isinstance(step_result, StepFileResponse)
                    or not step_result.status == StepStatus.NOT_READY
                ):
                    state.release_action_lock(state=state, action=action_request)

            except Exception as e:
                # * Handle any exceptions that occur while processing the action request,
                # * which should put the module in the ERROR state
                state.exception_handler(state, e)
                step_result = StepResponse.step_failed(
                    error=f"An exception occurred while processing the action request '{action_request.name}' with arguments '{action_request.args}: {e}"
                )
            print(step_result)
            return step_result

        # * Include the router in the main app
        self.app.include_router(self.router)

    def start(self):
        """Starts the REST server-based module"""
        import uvicorn

        # * Initialize the state object with all non-private attributes
        for attr in dir(self):
            if attr in ["start", "state", "app", "router"]:
                # * Skip wrapper- or server-only methods/attributes
                continue
            self.state.__setattr__(attr, getattr(self, attr))

        # * If arguments are passed, set them as state variables
        args = self.arg_parser.parse_args()
        for arg_name in vars(args):
            if (
                getattr(args, arg_name) is not None
            ):  # * Don't override already set attributes with None's
                self.state.__setattr__(arg_name, getattr(args, arg_name))
        self._configure_routes()

        # * Enforce a name
        if not self.state.name:
            raise Exception("A unique --name is required")
        import colorama

        colorama.just_fix_windows_console()
        uvicorn.run(self.app, host=self.state.host, port=self.state.port)


# Example usage
if __name__ == "__main__":
    rest_module = RESTModule(
        name="example_rest_node",
        version="0.0.1",
        description="An example REST module implementation",
        model="Example Instrument",
    )

    @rest_module.startup()
    def example_startup_handler(state: State):
        """Example startup handler."""
        print("Example startup handler. This is where I'd connect to instruments, etc.")
        print(f"Module Start Time: {time.time()}")

    @rest_module.action(name="succeed", description="An action that always succeeds")
    def succeed_action(state: State, action: ActionRequest) -> StepResponse:
        """Function to handle the "succeed" action. Always succeeds."""
        return StepResponse.step_succeeded(
            action_msg="Huzzah! The action was successful!",
            action_log=f"Succeeded: {time.time()}",
        )

    @rest_module.action(name="fail", description="An action that always fails")
    def fail_action(state: State, action: ActionRequest) -> StepResponse:
        """Function to handle the "fail" action. Always fails."""
        return StepResponse.step_failed(
            error=f"Failed: {time.time()}",
        )

    @rest_module.action(
        name="print", description="Action that prints the provided string."
    )
    def print_action(
        state: State,
        action: ActionRequest,
        output: Annotated[str, "What output to print to the console"],
    ) -> StepResponse:
        """Function to handle the "print" action."""
        print(output)
        return StepResponse.step_succeeded(
            action_msg=f"Printed {output}",
        )

    @rest_module.shutdown()
    def example_shutdown_handler(state: State):
        """Example startup handler."""
        print(
            "Example shutdown handler. This is where you'd disconnect from instruments, etc."
        )
        print(f"Module Shutdown Time: {time.time()}")

    @rest_module.safety_stop()
    def custom_safety_stop(state: State):
        """Custom safety-stop functionality"""
        print("Custom safety-stop functionality")
        return {"message": "Custom safety-stop functionality"}

    rest_module.start()
