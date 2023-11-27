"""
REST-based node that interfaces with WEI and provides a simple Sleep(t) function
"""
import json
import time
from argparse import ArgumentParser
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from wei.core.data_classes import ModuleStatus, StepResponse, StepStatus

workcell = None
global state


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initial run function for the app, parses the workcell argument
    Parameters
    ----------
    app : FastApi
       The REST API app being initialized

    Returns
    -------
    None"""
    global state
    try:
        state = ModuleStatus.IDLE
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
    """Returns the state of the module"""
    global state
    if state != ModuleStatus.BUSY:
        pass
    return JSONResponse(content={"State": state})


@app.get("/about")
async def about():
    """Returns information about the module and its capabilities"""
    global state
    return JSONResponse(content={"State": state})


@app.get("/resources")
async def resources():
    """Returns information about the resources this module handles"""
    global state
    return JSONResponse(content={"State": state})


@app.post("/action")
def do_action(
    action_handle: str,
    action_vars: str,
):
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
            action_response=StepStatus.Failed,
            action_msg="",
            action_log="Node is busy",
        )
    state = ModuleStatus.BUSY
    if action_handle:
        try:
            action_vars = json.loads(action_vars)
            print(type(action_vars))
            t = action_vars["t"]
            time.sleep(int(t))
            state = ModuleStatus.IDLE
            print("success")
            return StepResponse(
                action_response=StepStatus.SUCCEEDED,
                action_msg="True",
                action_log="",
            )
        except Exception as e:
            print(e)
            state = ModuleStatus.ERROR
            return StepResponse(
                action_response=StepStatus.FAILED,
                action_msg="False",
                action_log=str(e),
            )
    else:
        state = ModuleStatus.IDLE
        return StepResponse(
            action_response=StepStatus.FAILED,
            action_msg="False",
            action_log="Action not supported",
        )


if __name__ == "__main__":
    import uvicorn

    parser = ArgumentParser()
    parser.add_argument("--port", type=int, default="2000", help="Port for the Node")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Port for the Node")
    args = parser.parse_args()
    uvicorn.run(
        "dummy_rest_node:app",
        host=args.host,
        port=args.port,
        reload=True,
    )
