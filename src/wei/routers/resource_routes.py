"""API server for the Resource Manager"""

from typing import Dict, List

from fastapi import APIRouter

from wei.resources_interface import ResourceInterface
from wei.types.resource_types import (
    AssetTable,
    CollectionTable,
    PlateTable,
    PoolTable,
    QueueTable,
    ResourceContainerBase,
    StackTable,
)

router = APIRouter()
database_url = "sqlite:///database.db"


def get_resource_interface() -> ResourceInterface:
    """
    Dependency function to get the ResourceInterface.

    Returns:
        ResourceInterface: The resource interface with the default database URL.
    """
    return ResourceInterface(database_url)


@router.get("/up")
def is_server_up() -> Dict[str, bool]:
    """
    Check if the resource server is up
    """
    return {"up": True}


@router.get("/resources/{resource_type}")
def get_all_resources(
    resource_type: str,
):  # TODO: Make this get resources by type & create a new function for get all resources
    """
    Retrieve all resources of a specific type from the database.

    Args:
        resource_type (str): The type of resource to retrieve.

    Returns:
        List[ResourceContainer]: List of all resources of the specified type.
    """
    resource_interface: ResourceInterface = router.state.resource_interface
    resource_map = {
        "pool": PoolTable,
        "stack": StackTable,
        "queue": QueueTable,
        "plate": PlateTable,
        "collection": CollectionTable,
    }
    resource_class = resource_map.get(resource_type.lower())
    if resource_class:
        return resource_interface.get_all_resources(resource_class)
    else:
        return {"error": f"Invalid resource type: {resource_type}"}


@router.get("/assets")
def get_all_assets() -> List[AssetTable]:
    """
    Get all available assets
    """
    resource_interface: ResourceInterface = router.state.resource_interface
    return resource_interface.get_all_resources(AssetTable)


@router.get("/resource/{resource_type}/{resource_id}")
def get_resource_by_id(
    resource_type: str, resource_id: str
):  # TODO: don't use resource type
    """
    Get a resource by its ID and type.
    """
    resource_interface: ResourceInterface = router.state.resource_interface
    resource_map = {
        "pools": PoolTable,
        "stacks": StackTable,
        "queues": QueueTable,
        "plates": PlateTable,
        "collections": CollectionTable,
    }
    resource_class = resource_map.get(resource_type.lower())
    if resource_class:
        return resource_interface.get_resource(resource_class, resource_id)
    else:
        return {"error": f"Invalid resource type: {resource_type}"}


@router.get("/asset/{asset_id}")
def get_asset_by_id(asset_id: str) -> AssetTable:
    """
    Get an asset by its ID
    """
    resource_interface: ResourceInterface = router.state.resource_interface
    return resource_interface.get_resource(AssetTable, asset_id)


@router.post("/resource/{resource_type}")
def create_resource(
    resource_type: str, resource: ResourceContainerBase
):  # TODO: resource needs to be updated
    """
    Create a new resource of a specific type.
    """
    resource_interface: ResourceInterface = router.state.resource_interface
    resource_map = {
        "pools": PoolTable,
        "stacks": StackTable,
        "queues": QueueTable,
        "plates": PlateTable,
        "collections": CollectionTable,
    }
    resource_class = resource_map.get(resource_type.lower())
    if resource_class:
        return resource_interface.add_resource(resource)
    else:
        return {"error": f"Invalid resource type: {resource_type}"}


@router.post("/asset")
def create_asset(asset: AssetTable) -> AssetTable:
    """
    Create a new asset
    """
    resource_interface: ResourceInterface = router.state.resource_interface
    return resource_interface.add_resource(asset)


@router.put("/asset/{asset_id}")
def update_asset(asset_id: str, asset: AssetTable) -> AssetTable:
    """
    Update an asset
    """
    resource_interface: ResourceInterface = router.state.resource_interface
    return resource_interface.update_resource(AssetTable, asset_id, asset.dict())


@router.put("/resource/{resource_type}/{resource_id}")
def update_resource(resource_type: str, resource_id: str, updates: Dict[str, any]):
    """
    Update a resource by its ID and type.
    """
    resource_interface: ResourceInterface = router.state.resource_interface
    resource_map = {
        "pools": PoolTable,
        "stacks": StackTable,
        "queues": QueueTable,
        "plates": PlateTable,
        "collections": CollectionTable,
    }
    resource_class = resource_map.get(resource_type.lower())
    if resource_class:
        return resource_interface.update_resource(resource_class, resource_id, updates)
    else:
        return {"error": f"Invalid resource type: {resource_type}"}


@router.delete("/resource/{resource_type}/{resource_id}")
def delete_resource(resource_type: str, resource_id: str):
    """
    Delete a resource by its ID and type.
    """
    resource_interface: ResourceInterface = router.state.resource_interface
    resource_map = {
        "pools": PoolTable,
        "stacks": StackTable,
        "queues": QueueTable,
        "plates": PlateTable,
        "collections": CollectionTable,
    }
    resource_class = resource_map.get(resource_type.lower())
    if resource_class:
        return {
            "deleted": resource_interface.delete_resource(resource_class, resource_id)
        }
    else:
        return {"error": f"Invalid resource type: {resource_type}"}


@router.delete("/asset/{asset_id}")
def delete_asset(asset_id: str) -> AssetTable:
    """
    Delete an asset
    """
    resource_interface: ResourceInterface = router.state.resource_interface
    return {"deleted": resource_interface.delete_resource(AssetTable, asset_id)}


@router.put("/resources/{resource_id}/push")
def push_asset_to_resource(resource_id: str, asset: AssetTable) -> int:
    """
    Push an asset to a stack or queue resource
    """
    resource_interface: ResourceInterface = router.state.resource_interface
    resource_type = resource_interface.get_resource_type(resource_id)
    if resource_type == "StackTable":
        stack = resource_interface.get_resource(StackTable, resource_id)
        return resource_interface.push_to_stack(stack, asset)
    elif resource_type == "QueueTable":
        queue = resource_interface.get_resource(QueueTable, resource_id)
        return resource_interface.push_to_queue(queue, asset)
    else:
        return {"error": f"Invalid resource type for push operation: {resource_type}"}


@router.put("/resources/{resource_id}/pop")
def pop_asset_from_resource(resource_id: str) -> AssetTable:
    """
    Pop an asset from a stack or queue resource
    """
    resource_interface: ResourceInterface = router.state.resource_interface
    resource_type = resource_interface.get_resource_type(resource_id)
    if resource_type == "StackTable":
        stack = resource_interface.get_resource(StackTable, resource_id)
        return resource_interface.pop_from_stack(stack)
    elif resource_type == "QueueTable":
        queue = resource_interface.get_resource(QueueTable, resource_id)
        return resource_interface.pop_from_queue(queue)
    else:
        return {"error": f"Invalid resource type for pop operation: {resource_type}"}


@router.put("/resources/{resource_id}/increase")
def increase_resource_quantity(resource_id: str, quantity: float) -> float:
    """
    Increase the quantity in a Pool resource
    """
    resource_interface: ResourceInterface = router.state.resource_interface
    pool = resource_interface.get_resource(PoolTable, resource_id)
    resource_interface.increase_pool_quantity(pool, quantity)
    return pool.quantity


@router.put("/resources/{resource_id}/decrease")
def decrease_resource_quantity(resource_id: str, quantity: float) -> float:
    """
    Decrease the quantity in a Pool resource
    """
    resource_interface: ResourceInterface = router.state.resource_interface
    pool = resource_interface.get_resource(PoolTable, resource_id)
    resource_interface.decrease_pool_quantity(pool, quantity)
    return pool.quantity


@router.put("/resources/{resource_id}/insert")
def insert_asset_into_resource(
    resource_id: str, location: str, asset: AssetTable
) -> int:
    """
    Insert an asset into a Collection resource
    """
    resource_interface: ResourceInterface = router.state.resource_interface
    collection = resource_interface.get_resource(CollectionTable, resource_id)
    resource_interface.insert_into_collection(collection, location, asset)
    return len(collection.contents_dict)


@router.put("/resources/{resource_id}/retrieve")
def remove_asset_from_resource(resource_id: str, location: str) -> Dict[str, str]:
    """
    Retrieve an asset from a Collection resource
    """
    resource_interface: ResourceInterface = router.state.resource_interface
    collection = resource_interface.get_resource(CollectionTable, resource_id)
    asset = resource_interface.retrieve_from_collection(collection, location)
    return {"id": asset.id, "name": asset.name}


@router.put("/resources/{resource_id}/empty")
def empty_pool_resource(resource_id: str) -> float:
    """
    Empty a Pool resource by setting its quantity to zero.

    Args:
        resource_id (str): The ID of the pool resource to empty.

    Returns:
        float: The new quantity of the pool (which should be 0).
    """
    resource_interface: ResourceInterface = router.state.resource_interface
    pool = resource_interface.get_resource(PoolTable, resource_id)
    resource_interface.empty_pool(pool)
    return pool.quantity


@router.put("/resources/{resource_id}/fill")
def fill_pool_resource(resource_id: str) -> float:
    """
    Fill a Pool resource by setting its quantity to its capacity.

    Args:
        resource_id (str): The ID of the pool resource to fill.

    Returns:
        float: The new quantity of the pool (which should be its capacity).
    """
    resource_interface: ResourceInterface = router.state.resource_interface
    pool = resource_interface.get_resource(PoolTable, resource_id)
    resource_interface.fill_pool(pool)
    return pool.quantity
