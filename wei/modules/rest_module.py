"""REST Module Convenience Class"""

import argparse
import traceback
from contextlib import asynccontextmanager
from threading import Thread
from typing import List, Optional

from fastapi import APIRouter, FastAPI, Request, Response, UploadFile, status
from fastapi.datastructures import State

from wei.types import ModuleStatus
from wei.types.module_types import ModuleAbout, ModuleAction
from wei.types.step_types import ActionRequest, StepResponse


def handle_exception(
    state: State, exception: Exception, error_message: Optional[str] = None
):
    """This function is called whenever a module encounters an irrecoverable exception.
    It should handle the exception (print errors, etc.) and set the module status to ERROR."""
    if error_message:
        print(f"Error: {error_message}")
    traceback.print_exc()
    state.status = ModuleStatus.ERROR
    state.error = str(exception)


def get_action_lock(state: State, action: ActionRequest):
    """This function is used to ensure the module only performs actions when it is safe to do so.
    In most cases, this means ensuring the instrument is not currently acting
    and then setting the module's status to BUSY to prevent other actions from being taken for the duration.
    """
    if state.status == ModuleStatus.IDLE:
        state.status = ModuleStatus.BUSY
    else:
        raise Exception("Module is not ready to accept actions")


def release_action_lock(state: State, action: ActionRequest):
    """Releases the lock on the module. This should be called after an action is completed."""
    if state.status == ModuleStatus.BUSY:
        state.status = ModuleStatus.IDLE
    else:
        print("Tried to release action lock, but module is not BUSY.")


class RESTModule:
    """A convenience class for creating REST-powered WEI modules."""

    alias: Optional[str] = None
    """A unique name for this particular instance of this module.
    This is required, and should generally be set by the command line."""
    arg_parser: Optional[argparse.ArgumentParser] = None
    """An argparse.ArgumentParser object that can be used to parse command line arguments. If not set in the constructor, a default will be used."""
    initialize: Optional[callable] = None
    """A function that will be called during the module's startup to do any custom initialization required. This is where you would set up any instruments or other resources. It takes a State object as input"""
    deinitialize: Optional[callable] = None
    """A function that will be called during the module's shutdown to clean up any resources used by the module. It takes a State object as input"""
    about: Optional[ModuleAbout] = None
    """A ModuleAbout object that describes the module. This is used to provide information about the module to user's and WEI."""
    action_handler: Optional[callable] = None
    """A function that will be called whenever an action is requested from the module. This function should take a State and ActionRequest objects as input and return a StepResponse object."""
    description: str = ""
    """A description of the module. This is used in the default argparse.ArgumentParser object."""

    def __init__(
        self,
        arg_parser: Optional[argparse.ArgumentParser] = None,
        description: str = "",
        alias: Optional[str] = None,
        initialize: Optional[callable] = None,
        deinitialize: Optional[callable] = None,
        about: Optional[ModuleAbout] = None,
        action_handler: Optional[callable] = None,
        handle_exception: callable = handle_exception,
        get_action_lock: callable = get_action_lock,
        release_action_lock: callable = release_action_lock,
        **kwargs,
    ):
        """Creates an instance of the RESTModule class"""
        self.app = FastAPI(lifespan=RESTModule.lifespan)
        self.app.state = State(
            state={
                "alias": alias,
                "status": ModuleStatus.INIT,
                "initialize": initialize,
                "deinitialize": deinitialize,
                "error": None,
                "about": about,
                "action_handler": action_handler,
                "handle_exception": handle_exception,
                "get_action_lock": get_action_lock,
                "release_action_lock": release_action_lock,
                "description": description,
            }
        )
        self.state = self.app.state  # * Mirror the state object for easier access
        # * Insert any extra kwargs into the state object so the user can use them as needed
        for key, value in kwargs.items():
            self.state[key] = value
        self.router = APIRouter()
        if arg_parser:
            self.arg_parser = arg_parser
        else:
            self.arg_parser = argparse.ArgumentParser(description=description)
            self.arg_parser.add_argument(
                "--host",
                type=str,
                default="0.0.0.0",
                help="Hostname or IP address to bind to (0.0.0.0 for all interfaces)",
            )
            self.arg_parser.add_argument(
                "--port",
                type=int,
                default="2000",
                help="Hostname or IP address to bind to (0.0.0.0 for all interfaces)",
            )
            self.arg_parser.add_argument(
                "--alias",
                "--name",
                "--node_name",
                type=str,
                default=None,
                help="A unique name for this particular instance of this module",
            )

    @staticmethod
    def initialization_runner(state: State):
        """Runs the initialization function for the module in a non-blocking thread, with error handling"""
        try:
            # * If the module has a defined initialize function, call it on a non-blocking thread
            if state.initialize:
                if not callable(state.initialize):
                    raise TypeError("Initialize function is not callable")
                state.initialize(state=state)
        except Exception as exception:
            # * If an exception occurs during initialization, handle it and put the module in an error state
            state.handle_exception(state, exception, "Error during initialization")
        else:
            # * If everything goes well, set the module status to IDLE
            state.status = ModuleStatus.IDLE
            print(
                "Initialization completed successfully. Module is now ready to accept actions."
            )

    @asynccontextmanager
    @staticmethod
    async def lifespan(app: FastAPI):
        """Initializes the module, doing any instrument initialization and starting the REST app."""

        # * Run initialization on a separate thread so it doesn't block the rest server from starting
        # * (module won't accept actions until initialization is complete)
        Thread(target=RESTModule.initialization_runner, args=[app.state]).start()

        yield

        try:
            # * If the module has a defined deinitialize function, call it
            if app.state.deinitialize:
                if not callable(app.state.deinitialize):
                    raise TypeError("Deinitialize function is not callable")
                app.state.deinitialize(app.state)
        except Exception as exception:
            # * If an exception occurs during deinitialization, handle it so we at least see the error in logs/terminal
            app.state.handle_exception(
                app.state, exception, "Error during initialization"
            )

    def configure_routes(self):
        """Configure the API endpoints for the REST module"""

        @self.router.get("/state")
        async def state(request: Request):
            state = request.app.state
            return {"State": state.status}

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
                response.status_code = status.HTTP_501_NOT_IMPLEMENTED
                return {}

        @self.router.post("/action")
        def action(
            request: Request,
            action_handle: str,
            action_vars: Optional[str] = None,
            files: List[UploadFile] = [],  # noqa: B006
        ):
            """Handles incoming action requests to the module. Returns a StepResponse or StepFileResponse object."""
            action_request = ActionRequest(
                name=action_handle, args=action_vars, files=files
            )
            state = request.app.state

            # * Check if the module is ready to accept actions
            try:
                state.get_action_lock(state=state, action=action_request)
            except Exception as exception:
                error_message = f"Module is not ready to accept actions. Module Status: {state.status}"
                state.handle_exception(state, exception, error_message)
                return StepResponse.step_failed(action_log=error_message)

            # * Try to run the action_handler for this module
            if state.action_handler:
                try:
                    step_result = state.action_handler(
                        state=state, action=action_request
                    )
                    state.release_action_lock(state=state, action=action_request)
                except Exception as e:
                    # * Handle any exceptions that occur while processing the action request,
                    # * which should put the module in the ERROR state
                    state.handle_exception(state, e)
                    return StepResponse.step_failed(
                        action_log=f"An exception occurred while processing the action request: {e}"
                    )
                return step_result
            else:
                return StepResponse.step_failed(
                    action_log="No action handler is defined for this module."
                )

        # * Include the router in the main app
        self.app.include_router(self.router)

    def start(self):
        """Starts the REST server-based module"""

        # * If arguments are passed, set them as state variables
        args = self.arg_parser.parse_args()
        for arg_name in vars(args):
            self.app.state.__setattr__(arg_name, getattr(args, arg_name))
        self.configure_routes()
        import uvicorn

        # * Enforce a unique alias argument
        if not self.app.state.alias:
            raise Exception("A unique --alias is required")
        if not self.app.state.host:
            self.app.state.host = "0.0.0.0"
        if not self.app.state.port:
            self.app.state.port = 2000
        uvicorn.run(self.app, host=self.app.state.host, port=self.app.state.port)


# Example usage
if __name__ == "__main__":
    rest_module = RESTModule(
        alias="example_rest_node",
        description="An example REST module implementation",
        about=ModuleAbout(
            name="Example REST Module",
            version="0.1.0",
            actions=[ModuleAction(name="succeed")],
        ),
    )

    def action_handler(state: State, action: ActionRequest) -> StepResponse:
        """Example action handler that succeeds on command"""
        if action.name == "succeed":
            return StepResponse.step_succeeded(
                action_msg="Huzzah! The action was successful!"
            )
        else:
            return StepResponse.step_failed(
                action_msg="Oh no! The action failed!",
                action_log="This is a test log message",
            )

    rest_module.state.action_handler = action_handler
    rest_module.start()
