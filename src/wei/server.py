"""The server that takes incoming WEI flow requests from the experiment application"""

from contextlib import asynccontextmanager
from pathlib import Path
from typing import Dict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from wei import __version__
from wei.config import Config
from wei.core.events import EventHandler
from wei.core.storage import initialize_storage
from wei.engine import Engine
from wei.routers import (
    admin_routes,
    campaign_routes,
    data_routes,
    event_routes,
    experiment_routes,
    location_routes,
    module_routes,
    workcell_routes,
    workflow_routes,
)
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
    app.include_router(campaign_routes.router, prefix="/campaigns")
    app.include_router(event_routes.router, prefix="/events")
    app.include_router(location_routes.router, prefix="/locations")
    app.include_router(module_routes.router, prefix="/modules")
    app.include_router(workcell_routes.router, prefix="/workcells")
    app.include_router(workcell_routes.router, prefix="/wc")
    ui_files_path = Path("wei") / "src" / "ui" / "dist"
    if ui_files_path.exists():
        app.mount("/", StaticFiles(directory=ui_files_path, html=True))
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


@app.get("/up")
def is_server_up() -> Dict[str, bool]:
    """
    Check if the server is up
    """
    return {"up": True}


@app.get("/version")
def get_version() -> Dict[str, str]:
    """
    Get the version of WEI
    """
    return {"version": __version__}


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
