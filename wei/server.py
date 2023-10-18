"""The server that takes incoming WEI flow requests from the experiment application"""
from argparse import ArgumentParser
from contextlib import asynccontextmanager
from pathlib import Path

import yaml
from fastapi import FastAPI

from wei.core.workcell import Workcell
from wei.routers import experiments, locations, modules, runs, workcells
from wei.state_manager import StateManager


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
    parser = ArgumentParser()
    parser.add_argument(
        "--redis_host",
        type=str,
        help="url (no port) for Redis server",
        default="localhost",
    )
    parser.add_argument("--workcell", type=Path, help="Path to workcell file")
    parser.add_argument(
        "--kafka-server", type=str, help="Kafka server for logging", default=None
    )

    args = parser.parse_args()
    with open(args.workcell) as f:
        workcell = Workcell(workcell_def=yaml.safe_load(f))
    state_manager = StateManager(
        workcell.workcell.name, redis_host=args.redis_host, redis_port=6379
    )

    kafka_server = args.kafka_server

    app.kafka_server = kafka_server
    app.state_manager = state_manager
    app.workcell = workcell

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
        host="0.0.0.0",
        reload=False,
    )
