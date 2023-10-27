"""
REST-based node that interfaces with WEI and provides a USB camera interface
"""
import json
from argparse import ArgumentParser
from contextlib import asynccontextmanager

import cv2
from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse

from wei.core.data_classes import ModuleStatus, StepStatus

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
async def description():
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
):
    global state
    if state == ModuleStatus.BUSY:
        return JSONResponse(
            content={
                "action_response": StepStatus.FAILED,
                "action_msg": "",
                "action_log": "Module is busy",
            }
        )
    state = ModuleStatus.BUSY
    if action_handle == "take_picture":
        try:
            image_name = json.loads(action_vars)["image_name"]
            camera = cv2.VideoCapture(0)
            _, frame = camera.read()
            cv2.imwrite(image_name, frame)
            camera.release()

            state = ModuleStatus.IDLE
            print("success")
            return FileResponse(
                path=image_name,
                headers={
                    "action_response": StepStatus.SUCCEEDED,
                    "action_msg": f"{image_name}",
                    "action_log": "",
                },
            )
        except Exception as e:
            print(e)
            state = ModuleStatus.IDLE
            return JSONResponse(
                content={
                    "action_response": StepStatus.FAILED,
                    "action_msg": "",
                    "action_log": str(e),
                }
            )
    else:
        state = ModuleStatus.IDLE
        return JSONResponse(
            content={
                "action_response": StepStatus.FAILED,
                "action_msg": "",
                "action_log": "Action not supported",
            }
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
