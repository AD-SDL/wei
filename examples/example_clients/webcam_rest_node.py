"""The server that takes incoming WEI flow requests from the experiment application"""
import json
from argparse import ArgumentParser
from contextlib import asynccontextmanager
import time
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import JSONResponse


workcell = None
global state
serial_port = "/dev/ttyUSB1"
local_ip = "parker.alcf.anl.gov"
local_port = "8000"


def parse_args():
    pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    global state
    """Initial run function for the app, parses the worcell argument
        Parameters
        ----------
        app : FastApi
           The REST API app being initialized

        Returns
        -------
        None"""
    try:
        #           sealer = A4S_SEALER_DRIVER(serial_port)
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
    return JSONResponse(content={"State": state})  # sealer.get_status() })


@app.get("/description")
async def description():
    global state
    return JSONResponse(content={"State": state})  # sealer.get_status() })


@app.get("/resources")
async def resources():
    global state
    return JSONResponse(content={"State": state})  # sealer.get_status() })


@app.post("/action")
def do_action(
    action_handle: str,
    action_vars: str,
):
    global state
    if state == "BUSY":
        return
    state = "BUSY"
    if action_handle == "action" or True:
        try:
            time.sleep(5)
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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "a4s_sealer_REST:app",
        host=local_ip,
        port=local_port,
        reload=True,
        ws_max_size=100000000000000000000000000000000000000,
    )
