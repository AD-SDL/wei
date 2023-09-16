"""
REST-based node that interfaces with WEI and provides a USB camera interface
"""
from contextlib import asynccontextmanager
import cv2
from fastapi import FastAPI
from fastapi.responses import JSONResponse


workcell = None
global state
local_ip = "localhost"
local_port = "2000"


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
            "status": "failed",
            "error": "Node is busy",
        }
        return JSONResponse(content=response_content)
    state = "BUSY"
    if action_handle == "take_picture":
        try:
            image_name = action_vars["image_name"]
            camera = cv2.VideoCapture(0)
            _, frame = camera.read()
            cv2.imwrite(image_name, frame)
            camera.release()

            response_content = {
                "action_msg": "StepStatus.Succeeded",
                "action_response": "True",
                "action_log": "",
            }
            state = "IDLE"
            print("success")
            return JSONResponse(content=response_content)
        except Exception as e:
            response_content = {
                "status": "failed",
                "error": str(e),
            }
            print("failure")
            state = "IDLE"
            return JSONResponse(content=response_content)
    else:
        response_content = {
            "status": "failed",
            "error": "Invalid action_handle",
        }
        state = "IDLE"
        return JSONResponse(content=response_content)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "sleep_node_REST:app",
        host=local_ip,
        port=local_port,
        reload=True,
        ws_max_size=100000000000000000000000000000000000000,
    )
