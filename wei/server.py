"""The server that takes incoming WEI flow requests from the experiment application"""
from contextlib import asynccontextmanager

from fastapi import FastAPI

from wei.config import Config
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

    uvicorn.run(
        "wei.server:app",
        host=Config.server_host,
        port=Config.server_port,
        reload=False,
    )
