"""
REST-based node that interfaces with WEI and provides a USB camera interface
"""
import json
from argparse import ArgumentParser
from contextlib import asynccontextmanager

import cv2
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from wei.core.data_classes import (
    ModuleStatus,
    StepFileResponse,
    StepResponse,
    StepStatus,
)

global state


@asynccontextmanager
async def lifespan(app: FastAPI):
    global state
    """Initial run function for the app, initializes state
        Parameters
        ----------
        app : FastApi
           The REST API app being initialized

        Returns
        -------
        None"""
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
    global state
    return JSONResponse(content={"State": state})


@app.get("/about")
async def about():
    global state
    return JSONResponse(content={"State": state})


@app.get("/resources")
async def resources():
    global state
    return JSONResponse(content={"State": state})


@app.post("/action")
def do_action(
    action_handle: str,
    action_vars: str,
) -> StepResponse:
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
            image_name = json.loads(action_vars)["image_name"]
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
