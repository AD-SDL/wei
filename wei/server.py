"""The server that takes incoming WEI flow requests from the experiment application"""
import json
from contextlib import asynccontextmanager
from time import sleep

from fastapi import FastAPI, JSONResponse

from wei.config import Config
from wei.core.data_classes import (
    ModuleAbout,
    ModuleAction,
    ModuleActionArg,
    ModuleStatus,
    StepResponse,
    StepStatus,
)
from wei.helpers import parse_args
from wei.routers import (
    events,
    experiments,
    locations,
    modules,
    workcells,
    workflow_runs,
)


@asynccontextmanager  # type: ignore
async def lifespan(app: FastAPI) -> None:  # type: ignore[misc]
    """
    Initial run function for the app, parses the workcell argument

    Parameters
    ----------
    app : FastApi
        The REST API app being initialized
    Returns
    -------
    None
    """

    app.include_router(workflow_runs.router, prefix="/runs")
    app.include_router(experiments.router, prefix="/experiments")
    app.include_router(events.router, prefix="/events")
    app.include_router(locations.router, prefix="/locations")
    app.include_router(modules.router, prefix="/modules")
    app.include_router(workcells.router, prefix="/workcells")
    app.include_router(workcells.router, prefix="/wc")

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
    return JSONResponse(content={"State": ModuleStatus.READY})


@app.get("/about")
def get_about() -> ModuleAbout:
    """Returns a description of the actions and resources the module supports"""
    from wei import __version__

    return ModuleAbout(
        name=Config.workcell_name,
        description="Workflow Execution Interface",
        interface="wei_rest_node",
        version=__version__,
        actions=[
            ModuleAction(
                name="delay",
                args=[
                    ModuleActionArg(
                        name="seconds", type=["float", "int"], required=True
                    )
                ],
            )
        ],
        resource_pools=[],
    )


@app.get("/resources", status_code=501)
def resources() -> JSONResponse:
    """Returns the current resources available to the module"""
    pass


@app.get("/action")
def action(action_handle: str, action_vars: str) -> StepResponse:
    """
    Runs an action on the module

    Parameters
    ----------
    action_handle : str
       The name of the action to be performed
    action_vars : str
        Any arguments necessary to run that action.
        This should be a JSON dictionary encoded as a string.

    Returns
    -------
    response: StepResponse
       A response object containing the result of the action
    """
    # TODO: Implement workcell status
    status = ModuleStatus.READY
    if status == ModuleStatus.BUSY:
        return StepResponse(
            action_response=StepStatus.FAILED,
            action_msg="",
            action_log="Module is busy",
        )
    status = ModuleStatus.BUSY

    try:
        arg_dict = json.loads(action_vars)
        if action_handle == "delay":
            sleep(arg_dict["seconds"])
            return StepResponse(
                action_response=StepStatus.SUCCEEDED,
                action_msg="",
                action_log=f"Delayed workflow for {arg_dict['seconds']} seconds",
            )
        elif action_handle == "prompt":
            pass
        elif action_handle == "confirm":
            pass
        elif action_handle == "notify":
            pass
        else:
            # Handle Unsupported actions
            status = ModuleStatus.IDLE
            return StepResponse(
                action_response=StepStatus.FAILED,
                action_msg="",
                action_log="Unsupported action",
            )
    except Exception as e:
        print(str(e))
        status = ModuleStatus.IDLE
        return StepResponse(
            action_response=StepStatus.FAILED,
            action_msg="",
            action_log=str(e),
        )


if __name__ == "__main__":
    import uvicorn

    parse_args()
    uvicorn.run(
        "wei.server:app",
        host=Config.server_host,
        port=Config.server_port,
        reload=False,
    )
