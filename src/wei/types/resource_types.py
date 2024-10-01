"""Resources Data Classes"""

import warnings
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import ulid
from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    PrimaryKeyConstraint,
    UniqueConstraint,
    func,
)
from sqlmodel import Field as SQLField
from sqlmodel import Session, SQLModel

# Suppress all DeprecationWarnings
warnings.filterwarnings("ignore", category=DeprecationWarning)


class AssetBase(SQLModel):
    """
    Base class for assets with an ID and a name.

    Attributes:
        id (str): Unique identifier for the asset.
        name (str): Name of the asset.
        module_name (str): Module name of the asset.
    """

    id: str = SQLField(default_factory=lambda: str(ulid.new()), primary_key=True)
    name: str = SQLField(default="", nullable=False)
    module_name: str = SQLField(default="", nullable=True)
    unique_resource: bool = SQLField(
        default=True, nullable=False
    )  # New flag to determine uniqueness


class Asset(AssetBase, table=True):
    """
    Represents the asset table with relationships to other resources.

    Attributes:
        time_created (datetime): Timestamp when the asset is created.
        time_updated (datetime): Timestamp when the asset is last updated.
    """

    time_created: datetime = SQLField(
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )
    time_updated: datetime = SQLField(
        sa_column=Column(
            DateTime(timezone=True), onupdate=func.now(), server_default=func.now()
        )
    )

    def allocate_to_resource(
        self, resource_type: str, resource_id: str, index: str, session: Session
    ):
        """
        Allocate this asset to a specific resource.

        Args:
            resource_type (str): The type of the resource ('stack', 'queue', etc.).
            resource_id (str): The ID of the resource.
            index (int): The index of the asset in the resource (for ordering in lists).
            session (Session): SQLAlchemy session to use for saving.

        Raises:
            ValueError: If the asset is already allocated to a different resource.
        """
        existing_allocation = (
            session.query(AssetAllocation).filter_by(asset_id=self.id).first()
        )

        if self.unique_resource:
            # Handle uniqueness constraint for assets that must be unique in a resource
            if existing_allocation:
                # Check if the asset is already allocated to the same resource
                if (
                    existing_allocation.resource_type == resource_type
                    and existing_allocation.resource_id == resource_id
                    and existing_allocation.index == index
                ):
                    # The asset is already allocated to this resource, no need to do anything.
                    return
                else:
                    # The asset is already allocated to a different resource.
                    raise ValueError(
                        f"Asset {self.name, self.id} is already allocated to a different resource or violates uniqueness."
                    )

        # If unique_resource is False, allow multiple allocations
        else:
            if existing_allocation:
                # Allow asset to be allocated multiple times in different resources (or same resource if allowed)
                print(f"Asset {self.name} is non-unique; continuing with allocation.")

        # Update the module_name to match the resource being allocated
        resource = session.get(Asset, resource_id)
        if resource:
            self.module_name = (
                resource.module_name
            )  # Set the module_name of the asset to the resource's module_name

        # Create a new allocation for the asset
        new_allocation = AssetAllocation(
            asset_id=self.id,
            resource_type=resource_type,
            resource_id=resource_id,
            index=index,
        )
        session.add(new_allocation)

        # Update the asset's timestamp
        self.time_updated = datetime.now(timezone.utc)
        session.commit()

    def deallocate(self, session: Session):
        """
        Deallocate this asset from its current resource.

        Args:
            session (Session): SQLAlchemy session to use for saving.

        Raises:
            ValueError: If the asset is not allocated to any resource.
        """
        allocation = session.query(AssetAllocation).filter_by(asset_id=self.id).first()

        if allocation is None:
            raise ValueError(f"Asset {self.id} is not allocated to any resource.")

        # Deallocate and set the module_name to None (indicating the asset is no longer allocated)
        self.module_name = None
        self.time_updated = datetime.now(
            timezone.utc
        )  # Set time_updated to current time
        session.delete(allocation)
        session.commit()

    def delete_asset(self, session: Session):
        """
        Delete this asset and automatically remove any associated asset allocations.

        Args:
            session (Session): The current SQLAlchemy session.
        """
        session.delete(self)
        session.commit()


class AssetAllocation(SQLModel, table=True):
    """
    Table that tracks which asset is allocated to which resource.

    Attributes:
        asset_id (str): Foreign key referencing the Asset.
        resource_type (str): Type of resource (e.g., 'stack', 'queue').
        resource_id (str): ID of the resource to which the asset is allocated.
    """

    asset_id: str = SQLField(foreign_key="asset.id", nullable=False)
    resource_type: str = SQLField(nullable=False)
    resource_id: str = SQLField(nullable=False)
    index: str = SQLField(nullable=False)

    # Use a composite primary key
    __table_args__ = (
        UniqueConstraint(
            "asset_id",
            "resource_type",
            "resource_id",
            name="uix_asset_resource_allocation",
        ),
        PrimaryKeyConstraint("asset_id", "resource_type", "resource_id"),
    )


class ResourceContainerBase(AssetBase):
    """
    Base class for resource containers with common attributes.

    Attributes:
        description (str): Description of the resource container.
        capacity (Optional[float]): Capacity of the resource container.
        quantity (float): Current quantity of resources in the container.
    """

    description: str = SQLField(default="")
    capacity: Optional[float] = SQLField(default=None, nullable=True)
    quantity: float = SQLField(default=0.0)

    def save(self, session: Session):
        """
        Save the resource container to the database.

        Args:
            session (Session): SQLAlchemy session to use for saving.
        """
        if isinstance(self, Plate):
            # Handling the Plate as a Collection for database operations
            collection = (
                session.query(Collection)
                .filter_by(
                    name=self.name,
                    module_name=self.module_name,
                )
                .first()
            )

            if not collection:
                # Create a new Collection if it doesn't exist
                collection = Collection(
                    id=self.id,
                    name=self.name,
                    description=self.description,
                    capacity=self.capacity,
                    quantity=self.quantity,
                    module_name=self.module_name,
                    unique_resource=self.unique_resource,
                    is_plate=True,
                )
                session.add(collection)
            else:
                # Update the existing Collection attributes
                collection.description = self.description
                collection.capacity = self.capacity
                collection.quantity = self.quantity
                collection.module_name = self.module_name

            session.commit()
            session.refresh(collection)

            # Update the corresponding Asset (if it exists)
            asset = session.get(Asset, collection.id)
            if asset:
                asset.time_updated = datetime.now(timezone.utc)
                session.commit()

            return collection  # Return the updated Collection

        # Handle normal resources
        session.add(self)
        session.commit()

        # Update the corresponding Asset (if it exists)
        asset = session.get(Asset, self.id)
        if asset:
            asset.time_updated = datetime.now(timezone.utc)
            session.commit()

        session.refresh(self)
        return self  # Return the updated resource

    def add_resource(self, session: Session) -> "ResourceContainerBase":
        """
        Check if a resource with the same name and module_name exists.
        If it exists, return the existing resource. Otherwise, create the resource
        and link it with an Asset.

        Args:
            session (Session): SQLAlchemy session to use for database operations.

        Returns:
            ResourceContainerBase: The saved or existing resource.
        """
        # Handle Plate type as Collection
        if isinstance(self, Plate):
            print("Handling Plate as a Collection")

            # Check if the Plate (treated as Collection) already exists
            existing_resource = (
                session.query(Collection)
                .filter_by(name=self.name, module_name=self.module_name)
                .first()
            )

            # If unique_resource is True, check for existing Plate and return or raise an error
            if self.unique_resource:
                if existing_resource:
                    print(
                        f"Using existing collection resource: {existing_resource.name}"
                    )
                    return self  # Return the Plate object (don't create a duplicate)

            # If unique_resource is False, allow multiple plates with the same name
            if not self.unique_resource or not existing_resource:
                # Create a new Collection object from the Plate data
                collection_resource = Collection(
                    id=self.id,
                    name=self.name,
                    description=self.description,
                    capacity=self.capacity,
                    module_name=self.module_name,
                    quantity=self.quantity,
                    unique_resource=self.unique_resource,
                    is_plate=True,
                )

                session.add(collection_resource)
                session.commit()
                session.refresh(collection_resource)

                # Create and link an Asset entry for the resource
                asset = Asset(
                    name=collection_resource.name,
                    id=collection_resource.id,
                    module_name=collection_resource.module_name,
                    unique_resource=self.unique_resource,
                )
                session.add(asset)
                session.commit()
                session.refresh(asset)

                print(f"Added new collection resource: {collection_resource.name}")
                return self  # Returning the Plate object itself

        # Handle normal resources (non-Plate)
        existing_resource = (
            session.query(type(self))
            .filter_by(name=self.name, module_name=self.module_name)
            .first()
        )

        # If unique_resource is True, check for existing resource and return or raise an error
        if self.unique_resource:
            if existing_resource:
                print(f"Using existing resource: {existing_resource.name}")
                return existing_resource

        # If unique_resource is False, allow creating multiple resources with the same name
        if not self.unique_resource or not existing_resource:
            # If the resource doesn't exist, create and save a new one
            session.add(self)
            session.commit()
            session.refresh(self)

            # Automatically create and link an Asset entry for the resource
            asset = Asset(
                name=self.name,
                id=self.id,
                module_name=self.module_name,
                unique_resource=self.unique_resource,
            )
            session.add(asset)
            session.commit()
            session.refresh(asset)

            print(f"Added new resource: {self.name}")
            return self


class PoolBase(ResourceContainerBase):
    """
    Base class for pool resources with methods to manipulate quantities.
    """

    def increase(self, amount: float, session: Session) -> None:
        """
        Increase the quantity in the pool by the specified amount.

        Args:
            amount (float): The amount to increase by.
            session (Session): SQLAlchemy session to use for saving.

        Raises:
            ValueError: If the increase exceeds the pool's capacity.
        """
        if not self.capacity or self.quantity + amount <= self.capacity:
            self.quantity += amount
            self.save(session)
        else:
            raise ValueError("Exceeds capacity.")

    def decrease(self, amount: float, session: Session) -> None:
        """
        Decrease the quantity in the pool by the specified amount.

        Args:
            amount (float): The amount to decrease by.
            session (Session): SQLAlchemy session to use for saving.

        Raises:
            ValueError: If the decrease would result in a negative quantity.
        """
        if not self.capacity or self.quantity - amount >= 0:
            self.quantity -= amount
            self.save(session)
        else:
            raise ValueError("Cannot decrease quantity below zero.")

    def empty(self, session: Session) -> None:
        """
        Empty the pool, setting its quantity to zero.

        Args:
            session (Session): SQLAlchemy session to use for saving.
        """
        self.quantity = 0.0
        self.save(session)

    def fill(self, session: Session) -> None:
        """
        Fill the pool to its capacity.

        Args:
            session (Session): SQLAlchemy session to use for saving.

        Raises:
            ValueError: If the pool does not have a defined capacity.
        """
        if self.capacity:
            self.quantity = self.capacity
            self.save(session)
        else:
            raise ValueError("Cannot fill without a defined capacity.")


class Pool(PoolBase, table=True):
    """
    Table for storing pool resources.

    Attributes:
        assets (List["Asset"]): Relationship to the Asset.
    """


class StackBase(ResourceContainerBase):
    """
    Base class for stack resources with methods to push and pop assets.

    Attributes:
        contents (List[Dict[str, Any]]): List of assets in the stack, stored as JSONB.
    """

    def get_contents(self, session: Session) -> List[Asset]:
        """
        Fetch and return assets in the stack, ordered by their index.

        The assets are returned as a list, ordered by their index in ascending order.
        Args:
            session (Session): The database session passed from the interface layer.

        Returns:
            List[Asset]: A list of assets sorted by their index.
        """
        allocations = (
            session.query(AssetAllocation)
            .filter_by(resource_id=self.id, resource_type="stack")
            .order_by(func.cast(AssetAllocation.index, Integer).asc())
            .all()
        )

        # Return the assets as a list based on the sorted allocations
        return [session.get(Asset, alloc.asset_id) for alloc in allocations]

    def push(self, asset: Asset, session: Session) -> int:
        """
        Push a new asset onto the stack. Assigns the next available index.

        Args:
            asset (Asset): The asset to push onto the stack.
            session (Session): SQLAlchemy session passed from the interface layer.

        Returns:
            int: The new index of the pushed asset.
        """
        # Fetch the current contents (sorted by index)
        contents = self.get_contents(session)
        # Check if the capacity is exceeded
        if self.capacity and len(contents) >= self.capacity:
            raise ValueError(f"Stack {self.name} is full. Capacity: {self.capacity}")

        # Find the next available index
        if contents:
            max_index = (
                session.query(AssetAllocation)
                .filter_by(resource_id=self.id)
                .order_by(func.cast(AssetAllocation.index, Integer).desc())
                .first()
            )
            next_index = int(max_index.index) + 1
        else:
            next_index = 1  # If there are no contents, start with index 1

        # Allocate the asset to the stack with the next available index
        asset.allocate_to_resource(
            resource_type="stack",
            resource_id=self.id,
            index=str(next_index),
            session=session,
        )

        # Update the quantity based on the number of assets in the stack
        self.quantity = len(contents) + 1  # Increase quantity by 1
        self.save(session)

        return next_index

    def pop(self, session: Session) -> Asset:
        """
        Pop the last asset from the stack.

        Args:
            session (Session): SQLAlchemy session to use for saving.

        Returns:
            Any: The popped asset.

        Raises:
            ValueError: If the stack is empty or if the asset is not found.
        """
        # Fetch the current contents (sorted by index)
        contents = self.get_contents(session)

        if not contents:
            raise ValueError(f"Resource {self.name} is empty.")

        # Pop the last asset (LIFO)
        last_asset = contents[-1]

        # Deallocate the asset from this stack
        last_asset.deallocate(session)

        # Update the quantity after removing the asset
        self.quantity = len(contents) - 1  # Decrease quantity by 1
        self.save(session)

        return last_asset


class Stack(StackBase, table=True):
    """
    Table for storing stack resources.

    Attributes:
        assets (List["Asset"]): Relationship to the Asset.
    """


class QueueBase(ResourceContainerBase):
    """
    Base class for queue resources with methods to push and pop assets.

    Attributes:
        contents (List[Dict[str, Any]]): List of assets in the queue, stored as JSONB.
    """

    def get_contents(self, session: Session) -> List[Asset]:
        """
        Fetch and return assets in the queue, ordered by their index (FIFO).

        The assets are returned as a list, ordered by their index in ascending order.
        Args:
            session (Session): The database session passed from the interface layer.

        Returns:
            List[Asset]: A list of assets sorted by their index.
        """
        allocations = (
            session.query(AssetAllocation)
            .filter_by(
                resource_id=self.id, resource_type="queue"
            )  # Ensure resource_type is 'queue'
            .order_by(
                func.cast(AssetAllocation.index, Integer).asc()
            )  # Sorted by index (FIFO)
            .all()
        )

        # Return the assets based on the sorted allocations
        return [session.get(Asset, alloc.asset_id) for alloc in allocations]

    def push(self, asset: Asset, session: Session) -> int:
        """
        Push a new asset onto the queue.

        Args:
            asset (Any): The asset to push onto the queue.
            session (Session): SQLAlchemy session to use for saving.

        Returns:
            int: The index of the pushed asset.

        Raises:
            ValueError: If the queue is full.
        """
        # Fetch the current contents (sorted by index)
        contents = self.get_contents(session)
        # Check if the capacity is exceeded
        if self.capacity and len(contents) >= self.capacity:
            raise ValueError(f"Queue {self.name} is full. Capacity: {self.capacity}")

        # Find the next available index as an integer
        if contents:
            max_index = (
                session.query(AssetAllocation)
                .filter_by(resource_id=self.id)
                .order_by(func.cast(AssetAllocation.index, Integer).desc())
                .first()
            )
            next_index = int(max_index.index) + 1
        else:
            next_index = 1

        # Allocate the asset to the queue with the next available index
        asset.allocate_to_resource(
            resource_type="queue",
            resource_id=self.id,
            index=str(next_index),
            session=session,
        )

        # Update the quantity based on the number of assets in the queue
        self.quantity = len(contents) + 1  # Increase quantity by 1
        self.save(session)

        return next_index

    def pop(self, session: Session) -> Any:
        """
        Pop the first asset from the queue (FIFO).

        Args:
            session (Session): SQLAlchemy session to use for saving.

        Returns:
            Any: The popped asset.

        Raises:
            ValueError: If the queue is empty or if the asset is not found.
        """
        # Fetch the current contents (sorted by index)
        contents = self.get_contents(session)  # Get the current queue contents

        if not contents:
            raise ValueError(f"Resource {self.name} is empty.")  # Error raised here

        # Pop the first asset (FIFO)
        first_asset = contents[0]

        # Deallocate the asset from this queue
        first_asset.deallocate(session)

        # Update the quantity after removing the asset
        self.quantity = len(contents) - 1  # Decrease quantity
        self.save(session)

        return {
            "id": first_asset.id,
            "name": first_asset.name,
            "module_name": first_asset.module_name,
        }


class Queue(QueueBase, table=True):
    """
    Table for storing queue resources.

    Attributes:
        assets (List["Asset"]): Relationship to the Asset.
    """


class CollectionBase(ResourceContainerBase):
    """
    Base class for collection resources with methods to insert and retrieve assets.

    Attributes:
        contents (Dict[str, Any]): Dictionary of assets in the collection, stored as JSONB.
    """

    is_plate: bool = SQLField(
        default=False
    )  # Flag to indicate if this collection is a Plate

    def get_contents(self, session: Session) -> Dict[str, Asset]:
        """
        Fetch and return assets in the collection, with index serving as the dictionary key.

        The assets are returned as a dictionary, where the index is used as the key.
        Args:
            session (Session): The database session passed from the interface layer.

        Returns:
            Dict[str, Asset]: A dictionary of assets keyed by their index.
        """
        allocations = (
            session.query(AssetAllocation)
            .filter_by(resource_id=self.id, resource_type="collection")
            .all()
        )
        return {
            alloc.index: session.get(Asset, alloc.asset_id) for alloc in allocations
        }

    def insert(self, location: str, asset: Asset, session: Session) -> None:
        """
        Insert a new asset into the collection at the specified location.

        Args:
            location (int): The location in the collection to insert the asset.
            asset (Asset): The asset to insert.
            session (Session): SQLAlchemy session to use for saving.

        Raises:
            ValueError: If the collection is full.
        """
        # Check if the capacity is exceeded
        contents = self.get_contents(session)
        if self.capacity and len(contents) >= self.capacity:
            raise ValueError(
                f"Collection {self.name} is full. Capacity: {self.capacity}"
            )

        # Check if an asset is already at this location
        existing_allocation = (
            session.query(AssetAllocation)
            .filter_by(resource_id=self.id, resource_type="collection", index=location)
            .first()
        )

        if existing_allocation:
            raise ValueError(
                f"Location {location} is already occupied in collection {self.name}."
            )
        # Allocate the asset to the collection at the specified location (index)
        asset.allocate_to_resource(
            resource_type="collection",
            resource_id=self.id,
            index=str(location),  # Use string-based location
            session=session,
        )

        # Update the quantity based on the number of assets in the collection
        contents = self.get_contents(session)
        self.quantity = len(contents)  # Update the quantity
        self.save(session)

    def retrieve(self, location: str, session: Session) -> Optional[Dict[str, Any]]:
        """
        Retrieve an asset from the collection at the specified location.

        Args:
            location (int): The location in the collection to retrieve the asset from.
            session (Session): SQLAlchemy session to use for fetching and saving.

        Returns:
            Optional[Dict[str, Any]]: The retrieved asset data.

        Raises:
            ValueError: If the location is invalid or the asset is not found.
        """
        location_str = str(location)
        # Perform the query with string comparison
        allocation = (
            session.query(AssetAllocation)
            .filter_by(
                resource_id=self.id, resource_type="collection", index=location_str
            )
            .first()
        )

        if allocation:
            asset = session.get(Asset, allocation.asset_id)
            module_name = asset.module_name
            if asset:
                # Deallocate the asset from the collection
                asset.deallocate(session)
                # Update the quantity after removing the asset
                contents = self.get_contents(session)
                self.quantity = max(len(contents) - 1, 0)
                self.save(session)

                return {
                    "id": asset.id,
                    "name": asset.name,
                    "module_name": module_name,
                    "resource_type": "collection",
                    "location": location_str,
                }
            else:
                raise ValueError(
                    f"Asset with id '{allocation.asset_id}' not found in database."
                )
        else:
            raise ValueError(
                f"Location {location_str} not found in collection {self.name}."
            )


class Collection(CollectionBase, table=True):
    """
    Table for storing collection resources.

    Attributes:
        assets (List["Asset"]): Relationship to the Asset.
    """


class Plate(CollectionBase):
    """
    Base class for plate resources with methods to manage wells.

    Attributes:
        contents (Dict[str, Any]): Dictionary of wells in the plate, stored as JSONB.
        well_capacity (Optional[float]): Capacity of each well in the plate.
    """

    well_capacity: Optional[float] = None  # Capacity of each well

    def get_wells(self, session: Session) -> Dict[str, Pool]:
        """
        Fetch and return the wells in the plate. Wells are stored as Pool resources within the plate.

        Args:
            session (Session): The database session passed from the interface layer.

        Returns:
            Dict[str, Pool]: A dictionary of wells keyed by their location.
        """
        # Query the Pool table for all wells associated with this plate
        wells = session.query(Pool).filter_by(module_name=self.name).all()

        # Create a dictionary of wells, using the well ID (name) as the key
        wells_dict = {well.name: well for well in wells}

        return wells_dict

    def set_wells(self, wells_dict: Dict[str, float], session: Session):
        """
        Dynamically add or update wells in the plate using well_id and quantity.
        Wells are stored as Pool resources.

        Args:
            wells_dict (Dict[str, float]): A dictionary of well IDs and quantities.
            session (Session): SQLAlchemy session passed from the interface layer.
        """
        #  Find the corresponding collection for this plate
        collection = (
            session.query(Collection).filter_by(id=self.id, name=self.name).first()
        )

        # Iterate over wells to add or update them
        for well_id, quantity in wells_dict.items():
            # Check if the well already exists in the Collection
            existing_well = (
                session.query(Pool)
                .filter_by(name=well_id, module_name=self.name)
                .first()
            )
            if existing_well:
                # If the well exists, update its quantity
                existing_well.quantity = quantity
                session.commit()
            else:
                # Create a new Pool (well) if it doesn't exist
                new_well = Pool(
                    name=well_id,
                    description=f"Well {well_id}",
                    capacity=self.well_capacity,
                    quantity=quantity,
                    module_name=self.name,  # Plate's name as module_name
                    unique_resource=self.unique_resource,
                )
                session.add(new_well)
                session.commit()

                # Create an Asset entry for the new well
                asset = Asset(
                    name=new_well.name,
                    id=new_well.id,
                    module_name=new_well.module_name,
                    unique_resource=new_well.unique_resource,
                )
                session.add(asset)
                session.commit()

                # Insert the well into the Collection at the specified location
                collection.insert(location=str(well_id), asset=asset, session=session)

        # Update the Plate's total quantity and commit
        total_quantity = (
            session.query(func.sum(Pool.quantity))
            .filter(Pool.module_name == self.name)
            .scalar()
        )
        self.quantity = total_quantity
        session.commit()

    def increase_well(self, well_id: str, quantity: float, session: Session) -> None:
        """
        Increase the quantity of liquid in a specific well.

        Args:
            well_id (str): The ID of the well to update.
            quantity (float): The quantity to add to the well.
            session (Session): SQLAlchemy session passed from the interface layer.

        Raises:
            ValueError: If the addition exceeds the well's capacity.
        """
        existing_well = (
            session.query(Pool).filter_by(name=well_id, module_name=self.name).first()
        )

        if not existing_well:
            raise ValueError(f"Well {well_id} not found in plate {self.name}.")

        # Increase the quantity of the existing well
        existing_well.quantity += quantity

    def decrease_well(self, well_id: str, quantity: float, session: Session) -> None:
        """
        Decrease the quantity of liquid in a specific well.

        Args:
            well_id (str): The ID of the well to update.
            quantity (float): The quantity to decrease in the well.
            session (Session): SQLAlchemy session passed from the interface layer.

        Raises:
            ValueError: If the decrease would result in a negative quantity.
        """
        # Find the corresponding well (Pool) in the Collection
        existing_well = (
            session.query(Pool).filter_by(name=well_id, module_name=self.name).first()
        )

        if not existing_well:
            raise ValueError(f"Well {well_id} not found in plate {self.name}.")

        # Check if the well has sufficient quantity to decrease
        if existing_well.quantity < quantity:
            raise ValueError(
                f"Well {well_id} does not have enough quantity to decrease by {quantity}."
            )

        # Decrease the quantity of the existing well
        existing_well.quantity -= quantity
