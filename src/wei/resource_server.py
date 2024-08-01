"""API server for the Resource Manager"""

from argparse import ArgumentParser
from contextlib import asynccontextmanager
from typing import Dict

from fastapi import FastAPI

from wei.types.resource_types import Asset, ResourceContainer


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
    Check if the resource server is up
    """
    return {"up": True}


@app.get("/resources")
def get_all_resources() -> Dict[str, ResourceContainer]:
    """
    Get all available resources
    """
    pass


@app.get("/assets")
def get_all_assets() -> Dict[str, Asset]:
    """
    Get all available assets
    """
    pass


@app.get("/resource/{resource_id}")
def get_resource_by_id(resource_id: str) -> ResourceContainer:
    """
    Get a resource by its ID
    """
    pass


@app.get("/asset/{asset_id}")
def get_asset_by_id(asset_id: str) -> Asset:
    """
    Get an asset by its ID
    """
    pass


@app.post("/resource")
def create_resource(resource: ResourceContainer) -> ResourceContainer:
    """
    Create a new resource
    """
    pass


@app.post("/asset")
def create_asset(asset: Asset) -> Asset:
    """
    Create a new asset
    """
    pass


@app.put("/asset/{asset_id}")
def update_asset(asset_id: str, asset: Asset) -> Asset:
    """
    Update an asset
    """
    pass


@app.delete("/resource/{resource_id}")
def delete_resource(resource_id: str) -> ResourceContainer:
    """
    Delete a resource
    """
    pass


@app.delete("/asset/{asset_id}")
def delete_asset(asset_id: str) -> Asset:
    """
    Delete an asset
    """
    pass


@app.put("/resources/{resource_id}/push")
def push_asset_to_resource(resource_id: str, asset: Asset) -> int:
    """
    Push an asset to a stack resource
    """
    pass


@app.put("/resources/{resource_id}/pop")
def pop_asset_from_resource(resource_id: str) -> Asset:
    """
    Pop an asset from a stack resource
    """
    pass


@app.put("/resources/{resource_id}/increase")
def increase_resource_quantity(resource_id: str, quantity: float) -> float:
    """
    Increase the quantity in a Pool resource
    """
    pass


@app.put("/resources/{resource_id}/decrease")
def decrease_resource_quantity(resource_id: str, quantity: float) -> float:
    """
    Decrease the quantity in a Pool resource
    """
    pass


@app.put("/resources/{resource_id}/fill")
def fill_pool_resource(resource_id: str) -> float:
    """
    Fill a Pool resource to its capacity
    """
    pass


@app.put("/resources/{resource_id}/empty")
def empty_pool_resource(resource_id: str) -> float:
    """
    Empty a Pool resource
    """
    pass


@app.put("/resources/{resource_id}/insert")
def insert_asset_into_resource(resource_id: str, asset: Asset) -> int:
    """
    Insert an asset into a Collection resource
    """
    pass


@app.put("/resources/{resource_id}/retrieve")
def remove_asset_from_resource(resource_id: str, asset_id: str) -> Asset:
    """
    Retrieve an asset from a Collection resource
    """
    pass


if __name__ == "__main__":
    import uvicorn

    parser = ArgumentParser()
    parser.add_argument(
        "--host", type=str, help="Host for the resource server", default="0.0.0.0"
    )
    parser.add_argument(
        "--port", type=str, help="Port for the resource server", default="8001"
    )
    args = parser.parse_args()

    uvicorn.run(
        "wei.resource_server:app",
        host=args.host,
        port=args.port,
        reload=False,
    )