"""Types for Resources and Assets"""

from enum import Enum
from typing import Dict, List, Optional, Union

from pydantic import Field

from wei.types.base_types import BaseModel, ulid_factory


class AssetStatus(str, Enum):
    """Status for an asset"""

    NEW = "new"
    IN_USE = "in_use"
    MISSING = "missing"
    DESTROYED = "destroyed"


class Resource(BaseModel, extra="allow"):
    """Resource Definition, a generic object of which Assets are instances"""

    id: str = Field(default_factory=ulid_factory)
    """Unique identifier for the resource"""
    name: str
    """Name of the resource"""
    parent_resources: Optional[List[Union[str, "Resource"]]] = None
    """Resources this resource inherits from, if any"""
    properties: dict = {}
    """Any custom properties of the resource"""


class Asset(BaseModel, extra="allow"):
    """Asset definition, a unique, trackable instance of a Resource"""

    id: str = Field(default_factory=ulid_factory)
    """Unique identifier for the asset"""
    name: str
    """Name of the asset"""
    resource: Union[str, Resource]
    """ID or definition of the resource this asset is an instance of"""
    location: Optional[str] = None
    """Current location of the asset"""
    status: AssetStatus = Field(default=AssetStatus.NEW)
    """Current status of the asset"""
    experiment_id: Optional[str] = None
    """Experiment this asset is associated with, if any"""
    metadata: dict = {}
    """Any additional metadata about the asset"""
    properties: dict = {}
    """Any custom properties of the asset"""


class DiscreteResourcePool(Asset, extra="allow"):
    """A resource pool, which contains discrete quantities of a generic resource"""

    quantity: int
    """Number of assets in the pool"""
    capacity: Optional[int] = None
    """Maximum number of assets that can be in the pool"""
    resource: Union[str, Resource]
    """ID or definition of the resource this pool currently contains"""
    supported_resources: list[Union[Resource, str]]
    """List of resources supported by the pool"""


class ContinuousResourcePool(Asset, extra="allow"):
    """A resource pool, which contains continuous quantities of a generic resource"""

    amount: float
    """Amount of the resource in the pool"""
    capacity: Optional[float] = None
    """Maximum amount of the resource that can be in the pool"""
    resource: Union[str, Resource]
    """ID or definition of the resource this pool currently contains"""
    supported_resources: list[Union[Resource, str]]
    """List of resources supported by the pool"""


class AssetCollection(Asset, extra="allow"):
    """Collections of assets that can be interacted with on demand"""

    supported_resources: list[Union[Resource, str]]
    """List of resources supported by the pool"""
    assets: Dict[str, Union[str, Asset]]
    """Dictionary of assets in the pool, keyed by asset ID"""
    capacity: Optional[int] = None
    """Maximum number of assets that can be in the pool"""


class AssetStack(Asset, extra="allow"):
    """Collection of assets that must be interacted with in a specific order"""

    supported_resources: list[Union[Resource, str]]
    """List of resources supported by the pool"""
    assets: List[Union[str, Asset]]
    """List of assets in the pool, in First-In-Last-Out (FILO) order"""
    capacity: Optional[int] = None
    """Maximum number of assets that can be in the pool"""


class AssetQueue(Asset, extra="allow"):
    """Collection of assets that must be interacted with in a specific order"""

    supported_resources: list[Union[Resource, str]]
    """List of resources supported by the pool"""
    assets: List[Union[str, Asset]]
    """List of assets in the pool, in First-In-First-Out (FIFO) order"""
    capacity: Optional[int] = None
    """Maximum number of assets that can be in the pool"""
