"""The server that takes incoming WEI flow requests from the experiment application"""

from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, Request, UploadFile
from fastapi.datastructures import State
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from wei import __version__
from wei.config import Config
from wei.core.events import EventHandler
from wei.core.state_manager import state_manager
from wei.core.storage import initialize_storage
from wei.core.workcell_actions import WorkcellActions
from wei.engine import Engine
from wei.modules.rest_module import RESTModule
from wei.routers import (
    admin_routes,
    data_routes,
    event_routes,
    experiment_routes,
    location_routes,
    module_routes,
    workcell_routes,
    workflow_routes,
)
from wei.types.module_types import AdminCommands, ModuleAbout, ModuleState
from wei.types.step_types import ActionRequest, StepResponse
from wei.utils import parse_args


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
    app.include_router(admin_routes.router, prefix="/admin")
    app.include_router(data_routes.router, prefix="/data")
    app.include_router(workflow_routes.router, prefix="/runs")
    app.include_router(experiment_routes.router, prefix="/experiments")
    app.include_router(event_routes.router, prefix="/events")
    app.include_router(location_routes.router, prefix="/locations")
    app.include_router(module_routes.router, prefix="/modules")
    app.include_router(workcell_routes.router, prefix="/workcells")
    app.include_router(workcell_routes.router, prefix="/wc")
    app.mount("/", StaticFiles(directory="wei/src/ui/dist", html=True))
    EventHandler.initialize_diaspora()

    if Config.autostart_engine:
        engine = Engine()
        engine.start_engine_thread()

    # Yield control to the application
    yield

    # Do any cleanup here
    pass


app = FastAPI(
    lifespan=lifespan,
)

app.state = State(
    state={
        "actions": WorkcellActions.actions,
        "action_handler": RESTModule.action_handler,
    }
)


@app.get("/up")
def is_server_up() -> Dict[str, bool]:
    """
    Check if the server is up
    """
    return {"up": True}


@app.get("/about")
def workcell_about() -> ModuleAbout:
    """
    Get information about the workcell
    """
    wc = state_manager.get_workcell()
    return {
        "name": Config.workcell_name,
        "model": "WEI Workcell",
        "interface": "wei_rest_interface",
        "description": wc.metadata.description,
        "version": str(wc.metadata.version),
        "wei_version": __version__,
        "actions": WorkcellActions.actions,
        "admin_commands": [command for command in AdminCommands],
    }


@app.get("/state")
def workcell_state() -> ModuleState:
    """
    Get the current state of the workcell
    """
    return ModuleState(
        status=state_manager.wc_status,
        error=state_manager.error,
    )


@app.get("/resources")
def workcell_resources() -> Dict[str, Any]:
    """
    Get the resources available to the workcell
    """
    return {}


@app.get("/action")
def workcell_action(
    request: Request,
    action_handle: str,
    action_vars: Optional[str] = None,
    files: List[UploadFile] = [],  # noqa: B006
) -> StepResponse:
    """Executes an action on the workcell"""
    action_request = ActionRequest(name=action_handle, args=action_vars, files=files)
    state = request.app.state

    # * Try to run the action_handler for this module
    try:
        step_result = state.action_handler(state=state, action=action_request)
    except Exception as e:
        # * Handle any exceptions that occur while processing the action request,
        # * which should put the module in the ERROR state
        state_manager.error = str(e)
        step_result = StepResponse.step_failed(
            error=f"An exception occurred while processing the action request '{action_request.name}' with arguments '{action_request.args}: {e}"
        )
    return step_result


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    import uvicorn

    parse_args()
    initialize_storage()
    uvicorn.run(
        "wei.server:app",
        host=Config.server_host,
        port=Config.server_port,
        reload=False,
    )
