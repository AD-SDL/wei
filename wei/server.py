"""The server that takes incoming WEI flow requests from the experiment application"""
from contextlib import asynccontextmanager

from fastapi import FastAPI

from wei.config import Config
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


if __name__ == "__main__":
    import uvicorn

    parse_args()
    uvicorn.run(
        "wei.server:app",
        host=Config.server_host,
        port=Config.server_port,
        reload=False,
    )
