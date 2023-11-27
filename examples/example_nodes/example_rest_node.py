"""Example REST-based client for a WEI module"""
import json
from argparse import ArgumentParser
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from wei.core.data_classes import (
    ModuleStatus,
    StepFileResponse,
    StepResponse,
    StepStatus,
)

global state, module_resources


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initial run function for the app, initializes the state
    Parameters
    ----------
    app : FastApi
       The REST API app being initialized

    Returns
    -------
    None"""
    global state, module_resources
    try:
        # Do any instrument configuration here
        state = ModuleStatus.IDLE
        module_resources = []
    except Exception as err:
        print(err)
        state = ModuleStatus.ERROR

    # Yield control to the application
    yield

    # Do any cleanup here
    pass


app = FastAPI(
    lifespan=lifespan,
)


@app.get("/state")
def get_state():
    """Returns the current state of the module"""
    global state
    return JSONResponse(content={"State": state})


@app.get("/about")
async def about():
    """Returns a description of the actions and resources the module supports"""
    global state
    return JSONResponse(content={"About": ""})


@app.get("/resources")
async def resources():
    """Returns the current resources available to the module"""
    global state, module_resources
    return JSONResponse(content={"Resources": module_resources})


@app.post("/action")
def do_action(
    action_handle: str,
    action_vars: str,
) -> StepResponse:
    """
    Runs an action on the module

    Parameters
    ----------
    action_handle : str
       The name of the action to be performed
    action_vars : str
        Any arguments necessary to run that action.
        This should be a JSON object encoded as a string.

    Returns
    -------
    response: StepResponse
       A response object containing the result of the action
    """
    global state
    if state == ModuleStatus.BUSY:
        return StepResponse(
            action_response=StepStatus.FAILED,
            action_msg="",
            action_log="Module is busy",
        )
    state = ModuleStatus.BUSY

    try:
        if action_handle == "do_action":
            ###
            # Your action execution logic goes here
            ###
            result = "any result you want to return"

            state = ModuleStatus.IDLE
            return StepResponse(
                action_response=StepStatus.SUCCEEDED,
                action_msg=result,
                action_log="",
            )
        elif action_handle == "do_action_return_file":
            state = ModuleStatus.IDLE
            # Use the FileResponse class to return files
            file_name = json.loads(action_vars)["file_name"]
            return StepFileResponse(
                action_response=StepStatus.SUCCEEDED,
                path=file_name,  # The path to the file to be returned
                action_log="",
            )
        else:
            # Handle Unsupported actions
            state = ModuleStatus.IDLE
            return StepResponse(
                action_response=StepStatus.FAILED,
                action_msg="",
                action_log="Unsupported action",
            )
    except Exception as e:
        print(str(e))
        state = ModuleStatus.IDLE
        return StepResponse(
            action_response=StepStatus.FAILED,
            action_msg="",
            action_log=str(e),
        )


if __name__ == "__main__":
    import uvicorn

    parser = ArgumentParser()
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host IP")
    parser.add_argument("--port", type=str, default="2000", help="Host IP")
    # Add any additional arguments here
    args = parser.parse_args()

    uvicorn.run(
        "example_rest_node:app",
        host=args.host,
        port=int(args.port),
        reload=True,
    )
