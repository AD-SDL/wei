"""
REST-based node that interfaces with WEI and provides a USB camera interface
"""
import json
from argparse import ArgumentParser
from contextlib import asynccontextmanager
from typing import Union

import cv2
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from wei.core.data_classes import (
    ModuleStatus,
    StepFileResponse,
    StepResponse,
    StepStatus,
)

state: ModuleStatus


@asynccontextmanager  # type: ignore
async def lifespan(app: FastAPI) -> None:
    """Initial run function for the app, initializes state
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
def get_state() -> JSONResponse:
    """Returns the current state of the module"""
    global state
    return JSONResponse(content={"State": state})


@app.get("/about")
async def about() -> JSONResponse:
    """Returns a description of the actions and resources the module supports"""
    global state
    return JSONResponse(content={"State": state})


@app.get("/resources")
async def resources() -> JSONResponse:
    """Returns the current resources available to the module"""
    global state
    return JSONResponse(content={"State": state})


@app.post("/action", response_model=None)
def do_action(
    action_handle: str,
    action_vars: str,
) -> Union[StepResponse, StepFileResponse]:
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
        if action_handle == "take_picture":
            image_name = json.loads(action_vars)["file_name"]
            camera = cv2.VideoCapture(0)
            _, frame = camera.read()
            cv2.imwrite(image_name, frame)
            camera.release()

            state = ModuleStatus.IDLE
            print("success")
            return StepFileResponse(
                action_response=StepStatus.SUCCEEDED,
                path=image_name,
                action_log="",
            )
        else:
            state = ModuleStatus.IDLE
            return StepResponse(
                action_response=StepStatus.FAILED,
                action_msg="",
                action_log="Unsupported action",
            )
    except Exception as e:
        print(e)
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
    parser.add_argument("--port", type=str, default="2001", help="Port to serve on")
    args = parser.parse_args()

    uvicorn.run(
        "webcam_rest_node:app", host=args.host, port=int(args.port), reload=True
    )
