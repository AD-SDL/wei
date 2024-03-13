"""
REST-based node that interfaces with WEI and provides various fake actions for testing purposes
"""
import json
from argparse import ArgumentParser
from contextlib import asynccontextmanager
from typing import List

from fastapi import FastAPI, UploadFile
from fastapi.responses import JSONResponse

from wei.core.data_classes import (
    ModuleAbout,
    ModuleAction,
    ModuleActionArg,
    ModuleActionFile,
    ModuleStatus,
    StepResponse,
    StepStatus,
)

parser = ArgumentParser()
parser.add_argument("--port", type=int, default="2000", help="Port for the Node")
parser.add_argument("--host", type=str, default="0.0.0.0", help="Hostname for the Node")
parser.add_argument(
    "--alias", type=str, default="test_rest_node", help="Alias for the Node"
)
args = parser.parse_args()

global state, foobar, alias


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
    global state, alias, foobar
    try:
        state = ModuleStatus.IDLE
        alias = args.alias
        foobar = 0.0
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
    global state, foobar
    return JSONResponse(content={"State": state, "foobar": foobar})


@app.get("/about")
async def about():
    """Returns information about the module and its capabilities"""
    global state
    global alias
    return ModuleAbout(
        name=alias,
        description="A test module for WEI",
        version="0.0.1",
        interface="wei_rest_node",
        resource_pools=[],
        model="test_module",
        actions=[
            ModuleAction(
                name="synthesize",
                description="Synthesizes a sample",
                args=[
                    ModuleActionArg(
                        name="foo",
                        description="How much foo to use",
                        required=True,
                        type="float",
                    ),
                    ModuleActionArg(
                        name="bar",
                        description="How much bar to use",
                        required=True,
                        type="float",
                    ),
                ],
                files=[
                    ModuleActionFile(
                        name="protocol",
                        required=True,
                        description="Python Protocol File",
                    )
                ],
            ),
            ModuleAction(
                name="measure",
                description="Measures the foobar of the current sample",
                args=[],
            ),
            ModuleAction(
                name="transfer",
                description="Synthesizes a sample",
                args=[
                    ModuleActionArg(
                        name="source",
                        description="Location to transfer sample from",
                        required=False,
                        type="Location",
                        default="[0, 0, 0, 0, 0, 0, 0]",
                    ),
                    ModuleActionArg(
                        name="target",
                        description="Location to transfer sample to",
                        required=True,
                        type="Location",
                    ),
                ],
            ),
        ],
    )


@app.get("/resources")
async def resources():
    """Returns information about the resources this module handles"""
    global state
    return JSONResponse(content={"State": state})


@app.post("/action")
def do_action(action_handle: str, action_vars: str, files: List[UploadFile] = []):  # noqa: B006
    """
    Runs an action on the module

    Parameters
    ----------
    action_handle : str
       The name of the action to be performed
    action_vars : str
        Any arguments necessary to run that action.
        This should be a JSON object encoded as a string.
    files: List[UploadFile] = []
        Any files necessary to run the action defined by action_handle.

    Returns
    -------
    response: StepResponse
       A response object containing the result of the action
    """
    global state, foobar
    if state == ModuleStatus.BUSY:
        return StepResponse(
            action_response=StepStatus.Failed,
            action_msg="",
            action_log="Node is busy",
        )
    state = ModuleStatus.BUSY
    try:
        if action_handle == "synthesize":
            action_vars = json.loads(action_vars)
            foo = float(action_vars["foo"])
            bar = float(action_vars["bar"])
            protocol = next(file for file in files if file.filename == "protocol")
            protocol = protocol.file.read().decode("utf-8")
            print(protocol)

            foobar = foo + bar

            state = ModuleStatus.IDLE
            return StepResponse(
                action_response=StepStatus.SUCCEEDED,
                action_msg="",
                action_log="Synthesized sample {foo} + {bar}",
            )
        elif action_handle == "measure":
            action_vars = json.loads(action_vars)

            state = ModuleStatus.IDLE
            return StepResponse(
                action_response=StepStatus.SUCCEEDED,
                action_msg=str(foobar),
                action_log="",
            )
        elif action_handle == "transfer":
            action_vars = json.loads(action_vars)
            source = action_vars.get("source", None)
            target = action_vars["target"]

            state = ModuleStatus.IDLE
            return StepResponse(
                action_response=StepStatus.SUCCEEDED,
                action_msg="",
                action_log=f"Moved sample from {source} to {target}",
            )
        else:
            state = ModuleStatus.IDLE
            return StepResponse(
                action_response=StepStatus.FAILED,
                action_msg="False",
                action_log=f"Action {action_handle} not supported",
            )
    except Exception as e:
        print(e)
        state = ModuleStatus.ERROR
        return StepResponse(
            action_response=StepStatus.FAILED,
            action_msg="False",
            action_log=str(e),
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "test_rest_node:app",
        host=args.host,
        port=args.port,
        reload=True,
    )
