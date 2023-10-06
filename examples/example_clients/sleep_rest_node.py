"""
REST-based node that interfaces with WEI and provides a simple Sleep(t) function
"""
import json
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse

workcell = None
global state
host = "0.0.0.0" # Allows all connections from local network
local_port = 2000


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
    if action_handle == "sleep":
        try:
            action_vars = json.loads(action_vars)
            print(type(action_vars))
            t = action_vars["t"]
            time.sleep(int(t))
            response_content = {
                "action_msg": "StepStatus.Succeeded",
                "action_response": "True",
                "action_log": "",
            }
            state = "IDLE"
            print("success")
            return JSONResponse(content=response_content)
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
        "sleep_rest_node:app",
        host=host,
        port=local_port,
        reload=True,
        ws_max_size=100000000000000000000000000000000000000,
    )
