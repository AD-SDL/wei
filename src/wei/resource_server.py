"""API server for the Resource Manager"""

from argparse import ArgumentParser
from contextlib import asynccontextmanager
from typing import Dict

from fastapi import FastAPI

from wei.resources_interface import ResourceInterface
from wei.types.resource_types import Asset, ResourceContainer

database_url = "sqlite:///database.db"


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

    # Initialize the database and create tables
    resource_interface = ResourceInterface(database_url)
    resource_interface.create_db_and_tables()
    app.state.resource_interface = resource_interface

    # Yield control to the application
    yield

    # Do any cleanup here
    pass


app = FastAPI(
    lifespan=lifespan,
)


def get_resource_interface():
    """
    Dependency function to get the ResourceInterface from app state.

    Returns:
        ResourceInterface: The resource interface with the default database URL.
    """
    return app.state.resource_interface


@app.get("/up")
def is_server_up() -> Dict[str, bool]:
    """
    Check if the resource server is up
    """
    return {"up": True}


@app.get("/resources")
def get_all_resources():
    """
    Retrieve all resources from the database.

    Args:
        resource_interface (ResourceInterface): The resource interface instance.

    Returns:
        List[ResourceContainer]: List of all resources.
    """
    resource_interface: ResourceInterface = app.state.resource_interface
    return resource_interface.get_all_resources()


@app.get("/assets")
def get_all_assets() -> Dict[str, Asset]:
    """
    Get all available assets
    """
    resource_interface: ResourceInterface = app.state.resource_interface
    return resource_interface.get_all_assets()


@app.get("/resource/{resource_id}")
def get_resource_by_id(resource_id: str) -> ResourceContainer:
    """
    Get a resource by its ID
    """
    resource_interface: ResourceInterface = app.state.resource_interface
    return resource_interface.get_resource_by_id(resource_id)


@app.get("/asset/{asset_id}")
def get_asset_by_id(asset_id: str) -> Asset:
    """
    Get an asset by its ID
    """
    resource_interface: ResourceInterface = app.state.resource_interface
    return resource_interface.get_asset_by_id(asset_id)


@app.post("/resource")
def create_resource(resource: ResourceContainer) -> ResourceContainer:
    """
    Create a new resource
    """
    resource_interface: ResourceInterface = app.state.resource_interface
    return resource_interface.create_resource(resource)


@app.post("/asset")
def create_asset(asset: Asset) -> Asset:
    """
    Create a new asset
    """
    resource_interface: ResourceInterface = app.state.resource_interface
    return resource_interface.create_asset(asset)


@app.put("/asset/{asset_id}")
def update_asset(asset_id: str, asset: Asset) -> Asset:
    """
    Update an asset
    """
    resource_interface: ResourceInterface = app.state.resource_interface
    return resource_interface.update_asset(asset_id, asset)


@app.delete("/resource/{resource_id}")
def delete_resource(resource_id: str) -> ResourceContainer:
    """
    Delete a resource
    """
    resource_interface: ResourceInterface = app.state.resource_interface
    return resource_interface.delete_resource(resource_id)


@app.delete("/asset/{asset_id}")
def delete_asset(asset_id: str) -> Asset:
    """
    Delete an asset
    """
    resource_interface: ResourceInterface = app.state.resource_interface
    return resource_interface.delete_asset(asset_id)


@app.put("/resources/{resource_id}/push")
def push_asset_to_resource(resource_id: str, asset: Asset) -> int:
    """
    Push an asset to a stack resource
    """
    resource_interface: ResourceInterface = app.state.resource_interface
    return resource_interface.push_asset_to_resource(resource_id, asset)


@app.put("/resources/{resource_id}/pop")
def pop_asset_from_resource(resource_id: str) -> Asset:
    """
    Pop an asset from a stack resource
    """
    resource_interface: ResourceInterface = app.state.resource_interface
    return resource_interface.pop_asset_from_resource(resource_id)


@app.put("/resources/{resource_id}/increase")
def increase_resource_quantity(resource_id: str, quantity: float) -> float:
    """
    Increase the quantity in a Pool resource
    """
    resource_interface: ResourceInterface = app.state.resource_interface
    return resource_interface.increase_resource_quantity(resource_id, quantity)


@app.put("/resources/{resource_id}/decrease")
def decrease_resource_quantity(resource_id: str, quantity: float) -> float:
    """
    Decrease the quantity in a Pool resource
    """
    resource_interface: ResourceInterface = app.state.resource_interface
    return resource_interface.decrease_resource_quantity(resource_id, quantity)


@app.put("/resources/{resource_id}/fill")
def fill_pool_resource(resource_id: str) -> float:
    """
    Fill a Pool resource to its capacity
    """
    resource_interface: ResourceInterface = app.state.resource_interface
    return resource_interface.fill_pool_resource(resource_id)


@app.put("/resources/{resource_id}/empty")
def empty_pool_resource(resource_id: str) -> float:
    """
    Empty a Pool resource
    """
    resource_interface: ResourceInterface = app.state.resource_interface
    return resource_interface.empty_pool_resource(resource_id)


@app.put("/resources/{resource_id}/insert")
def insert_asset_into_resource(resource_id: str, asset: Asset) -> int:
    """
    Insert an asset into a Collection resource
    """
    resource_interface: ResourceInterface = app.state.resource_interface
    return resource_interface.insert_asset_into_resource(resource_id, asset)


@app.put("/resources/{resource_id}/retrieve")
def remove_asset_from_resource(resource_id: str, asset_id: str) -> Asset:
    """
    Retrieve an asset from a Collection resource
    """
    resource_interface: ResourceInterface = app.state.resource_interface
    return resource_interface.remove_asset_from_resource(resource_id, asset_id)


if __name__ == "__main__":
    import uvicorn

    parser = ArgumentParser()
    parser.add_argument(
        "--host", type=str, help="Host for the resource server", default="0.0.0.0"
    )
    parser.add_argument(
        "--port", type=str, help="Port for the resource server", default="8001"
    )
    parser.add_argument(
        "--database-url",
        type=str,
        help="Database URL for the resource server",
        default="sqlite:///database.db",
    )
    args = parser.parse_args()

    resource_interface = ResourceInterface(database_url=args.database_url)

    uvicorn.run(
        "wei.resource_server:app",
        host=args.host,
        port=args.port,
        reload=False,
    )
