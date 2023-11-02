"""The server that takes incoming WEI flow requests from the experiment application"""
from argparse import ArgumentParser
from contextlib import asynccontextmanager
from pathlib import Path

import yaml
from fastapi import FastAPI

from wei.core.config import Config, parse_args
from wei.core.data_classes import WorkcellData
from wei.core.state_manager import StateManager
from wei.routers import experiments, locations, modules, runs, workcells


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initial run function for the app, parses the workcell argument
        Parameters
        ----------
        app : FastApi
           The REST API app being initialized
    , timeout_sec=10
        Returns
        -------
        None"""

    app.include_router(runs.router, prefix="/runs")
    app.include_router(experiments.router, prefix="/experiments")
    app.include_router(experiments.router, prefix="/exp")
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


if __name__ == "__main__":
    import uvicorn

    args = parse_args()
    Config.load_server_config(args)

    uvicorn.run(
        "wei.server:app",
        host=Config.server_host,
        port=Config.server_port,
        reload=False,
    )
