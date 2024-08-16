"""API server for the Resource Manager"""

from typing import Any, Dict, List

from fastapi import APIRouter

from wei.config import Config
from wei.core.state_manager import StateManager
from wei.resources_interface import ResourceInterface
from wei.types.resource_types import (
    AssetTable,
    CollectionTable,
    PlateTable,
    PoolTable,
    QueueTable,
    StackTable,
)

router = APIRouter()
state_manager = StateManager()
state_manager.resource_interface = ResourceInterface(
    database_url=Config.resource_database_url
)


@router.get("/up")
def is_server_up() -> Dict[str, bool]:
    """
    Check if the resource server is up
    """
    return {"up": True}


@router.get("/resources/{resource_type}")
def get_all_resources(
    resource_type: str,
):
    """
    Retrieve all resources of a specific type from the database.

    Args:
        resource_type (str): The type of resource to retrieve.

    Returns:
        List[ResourceContainer]: List of all resources of the specified type.
    """
    resource_map = {
        "pool": PoolTable,
        "stack": StackTable,
        "queue": QueueTable,
        "plate": PlateTable,
        "collection": CollectionTable,
    }
    resource_class = resource_map.get(resource_type.lower())
    if resource_class:
        return state_manager.resource_interface.get_all_resources(resource_class)
    else:
        return {"error": f"Invalid resource type: {resource_type}"}


@router.get("/assets")
def get_all_assets() -> List[AssetTable]:
    """
    Get all available assets
    """
    return state_manager.resource_interface.get_all_resources(AssetTable)


@router.get("/resource/{resource_type}/{resource_id}")
def get_resource_by_id(resource_type: str, resource_id: str):
    """
    Get a resource by its ID and type.
    """
    resource_map = {
        "pools": PoolTable,
        "stacks": StackTable,
        "queues": QueueTable,
        "plates": PlateTable,
        "collections": CollectionTable,
    }
    resource_class = resource_map.get(resource_type.lower())
    if resource_class:
        return state_manager.resource_interface.get_resource(
            resource_class, resource_id
        )
    else:
        return {"error": f"Invalid resource type: {resource_type}"}


@router.get("/asset/{asset_id}")
def get_asset_by_id(asset_id: str) -> AssetTable:
    """
    Get an asset by its ID
    """
    return state_manager.resource_interface.get_resource(AssetTable, asset_id)


@router.post("/resource/{resource_type}")
def create_resource(resource_type: str, resource) -> Any:
    """
    Create a new resource of a specific type.
    """
    resource_map = {
        "pools": PoolTable,
        "stacks": StackTable,
        "queues": QueueTable,
        "plates": PlateTable,
        "collections": CollectionTable,
    }
    resource_class = resource_map.get(resource_type.lower())
    if resource_class:
        return state_manager.resource_interface.add_resource(resource)
    else:
        return {"error": f"Invalid resource type: {resource_type}"}


@router.post("/asset")
def create_asset(asset: AssetTable) -> AssetTable:
    """
    Create a new asset
    """
    return state_manager.resource_interface.add_resource(asset)


@router.put("/asset/{asset_id}")
def update_asset(asset_id: str, asset: AssetTable) -> AssetTable:
    """
    Update an asset
    """
    return state_manager.resource_interface.update_resource(
        AssetTable, asset_id, asset.model_dump()
    )


@router.put("/resource/{resource_type}/{resource_id}")
def update_resource(
    resource_type: str, resource_id: str, updates: Dict[str, Any]
) -> Any:
    """
    Update a resource by its ID and type.
    """
    resource_map = {
        "pools": PoolTable,
        "stacks": StackTable,
        "queues": QueueTable,
        "plates": PlateTable,
        "collections": CollectionTable,
    }
    resource_class = resource_map.get(resource_type.lower())
    if resource_class:
        return state_manager.resource_interface.update_resource(
            resource_class, resource_id, updates
        )
    else:
        return {"error": f"Invalid resource type: {resource_type}"}


@router.delete("/resource/{resource_type}/{resource_id}")
def delete_resource(resource_type: str, resource_id: str) -> Dict[str, Any]:
    """
    Delete a resource by its ID and type.
    """
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
            "deleted": state_manager.resource_interface.delete_resource(
                resource_class, resource_id
            )
        }
    else:
        return {"error": f"Invalid resource type: {resource_type}"}


@router.delete("/asset/{asset_id}")
def delete_asset(asset_id: str) -> Dict[str, Any]:
    """
    Delete an asset
    """
    return {
        "deleted": state_manager.resource_interface.delete_resource(
            AssetTable, asset_id
        )
    }


@router.put("/resources/{resource_id}/push")
def push_asset_to_resource(resource_id: str, asset: AssetTable) -> int:
    """
    Push an asset to a stack or queue resource
    """
    resource_type = state_manager.resource_interface.get_resource_type(resource_id)
    if resource_type == "StackTable":
        stack = state_manager.resource_interface.get_resource(StackTable, resource_id)
        return state_manager.resource_interface.push_to_stack(stack, asset)
    elif resource_type == "QueueTable":
        queue = state_manager.resource_interface.get_resource(QueueTable, resource_id)
        return state_manager.resource_interface.push_to_queue(queue, asset)
    else:
        return {"error": f"Invalid resource type for push operation: {resource_type}"}


@router.put("/resources/{resource_id}/pop")
def pop_asset_from_resource(resource_id: str) -> Any:
    """
    Pop an asset from a stack or queue resource
    """
    resource_type = state_manager.resource_interface.get_resource_type(resource_id)
    if resource_type == "StackTable":
        stack = state_manager.resource_interface.get_resource(StackTable, resource_id)
        return state_manager.resource_interface.pop_from_stack(stack)
    elif resource_type == "QueueTable":
        queue = state_manager.resource_interface.get_resource(QueueTable, resource_id)
        return state_manager.resource_interface.pop_from_queue(queue)
    else:
        return {"error": f"Invalid resource type for pop operation: {resource_type}"}


@router.put("/resources/{resource_id}/increase")
def increase_resource_quantity(resource_id: str, quantity: float) -> float:
    """
    Increase the quantity in a Pool resource
    """
    pool = state_manager.resource_interface.get_resource(PoolTable, resource_id)
    state_manager.resource_interface.increase_pool_quantity(pool, quantity)
    return pool.quantity


@router.put("/resources/{resource_id}/decrease")
def decrease_resource_quantity(resource_id: str, quantity: float) -> float:
    """
    Decrease the quantity in a Pool resource
    """
    pool = state_manager.resource_interface.get_resource(PoolTable, resource_id)
    state_manager.resource_interface.decrease_pool_quantity(pool, quantity)
    return pool.quantity


@router.put("/resources/{resource_id}/insert")
def insert_asset_into_resource(
    resource_id: str, location: str, asset: AssetTable
) -> int:
    """
    Insert an asset into a Collection resource
    """
    collection = state_manager.resource_interface.get_resource(
        CollectionTable, resource_id
    )
    state_manager.resource_interface.insert_into_collection(collection, location, asset)
    return len(collection.contents_dict)


@router.put("/resources/{resource_id}/retrieve")
def remove_asset_from_resource(resource_id: str, location: str) -> Dict[str, str]:
    """
    Retrieve an asset from a Collection resource
    """
    collection = state_manager.resource_interface.get_resource(
        CollectionTable, resource_id
    )
    asset = state_manager.resource_interface.retrieve_from_collection(
        collection, location
    )
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
    pool = state_manager.resource_interface.get_resource(PoolTable, resource_id)
    state_manager.resource_interface.empty_pool(pool)
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
    pool = state_manager.resource_interface.get_resource(PoolTable, resource_id)
    state_manager.resource_interface.fill_pool(pool)
    return pool.quantity
