"""The server that takes incoming WEI flow requests from the experiment application"""

from contextlib import asynccontextmanager
from typing import Dict

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

from wei.config import Config
from wei.core.events import EventHandler
from wei.helpers import parse_args
from wei.routers import (
    admin_routes,
    event_routes,
    experiment_routes,
    location_routes,
    module_routes,
    workcell_routes,
    workflow_routes,
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

    app.include_router(admin_routes.router, prefix="/admin")
    app.include_router(workflow_routes.router, prefix="/runs")
    app.include_router(experiment_routes.router, prefix="/experiments")
    app.include_router(event_routes.router, prefix="/events")
    app.include_router(location_routes.router, prefix="/locations")
    app.include_router(module_routes.router, prefix="/modules")
    app.include_router(workcell_routes.router, prefix="/workcells")
    app.include_router(workcell_routes.router, prefix="/wc")

    EventHandler.initialize_diaspora()

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

@app.websocket("/state/ws")
async def get_state(websocket: WebSocket) -> None:
    """

    Describes the state of the whole workcell including locations and daemon states

    Parameters
    ----------
    None

     Returns
    -------
     response: Dict
       the state of the workcell
    """
    print("start")
    
    await websocket.accept()
    
    print("test")
   
    # data = await websocket.receive_text()
    # EventHandler.log_event(Event(event_type="recieve", event_name=str(data)))
    await websocket.send_text({"testingtesing"})
   


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
    uvicorn.run(
        "wei.server:app",
        host=Config.server_host,
        port=Config.server_port,
        reload=False,
    )
