"""
REST-based node that interfaces with WEI and provides a USB camera interface
"""
import json
from contextlib import asynccontextmanager

import cv2
from fastapi import FastAPI
from fastapi.responses import JSONResponse, FileResponse

workcell = None
global state
host = "172.26.192.1"  # Allows all connections from local network
local_port = 2001


@asynccontextmanager
async def lifespan(app: FastAPI):
    global state
    """Initial run function for the app, parses the workcell argument
        Parameters
        ----------
        app : FastApi
           The REST API app being initialized

        Returns
        -------
        None"""
    try:
        state = "IDLE"
    except Exception as err:
        print(err)
        state = "ERROR"

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
    if state != "BUSY":
        pass
    return JSONResponse(content={"State": state})


@app.get("/description")
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
    if state == "BUSY":
        response_content = {
            "action_msg": "StepStatus.Failed",
            "action_response": "False",
            "action_log": "Node is busy",
        }
        return JSONResponse(content=response_content)
    state = "BUSY"
    if action_handle == "take_picture":
        try:
            image_name = json.loads(action_vars)["image_name"]
            camera = cv2.VideoCapture(0)
            _, frame = camera.read()
            cv2.imwrite(image_name, frame)
            camera.release()

            response_content = {
                "action_response": "StepStatus.Succeeded",
                "action_msg": "webcam_image.jpg",
                "action_log": "",
            }
            state = "IDLE"
            print("success")
            response = FileResponse(image_name, headers = response_content)
          
            return response
        except Exception as e:
            print(e)
            response_content = {
                "action_msg": "StepStatus.Failed",
                "action_response": "False",
                "action_log": str(e),
            }
            state = "IDLE"
            return JSONResponse(content=response_content)
    else:
        response_content = {
            "action_msg": "StepStatus.Failed",
            "action_response": "False",
            "action_log": "Action not supported",
        }
        state = "IDLE"
        return JSONResponse(content=response_content)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "webcam_rest_node:app",
        host=host,
        port=local_port,
        reload=True,
        ws_max_size=100000000000000000000000000000000000000,
    )
