"""Resources Data Classes"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import ulid
from sqlalchemy import Column, DateTime, Integer, UniqueConstraint, func
from sqlmodel import Field as SQLField
from sqlmodel import Session, SQLModel


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

        if existing_allocation:
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
                    f"Asset {self.id} is already allocated to a different resource."
                )

        # Update the module_name to match the resource being allocated
        resource = session.get(Asset, resource_id)
        if resource:
            self.module_name = (
                resource.module_name
            )  # Set the module_name of the asset to the resource's module_name

        # If no existing allocation, create a new one
        new_allocation = AssetAllocation(
            asset_id=self.id,
            resource_type=resource_type,
            resource_id=resource_id,
            index=index,
        )
        session.add(new_allocation)
        self.time_updated = datetime.now(
            timezone.utc
        )  # Set time_updated to current time
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
        # Deleting the asset
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

    asset_id: str = SQLField(primary_key=True, foreign_key="asset.id", nullable=False)
    resource_type: str = SQLField(nullable=False)
    resource_id: str = SQLField(nullable=False)
    index: str = SQLField(
        nullable=False
    )  # Index for sorting assets in list-like resources


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
        session.add(self)
        session.commit()

        asset = session.get(Asset, self.id)
        if asset:
            asset.time_updated = datetime.now(
                timezone.utc
            )  # Set time_updated to current time
            session.commit()

        session.refresh(self)


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

    __table_args__ = (
        UniqueConstraint("name", "module_name", name="uix_name_module_name_pool"),
    )


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
            .order_by(
                func.cast(AssetAllocation.index, Integer).asc()
            )  # Use SQLAlchemy's Integer type
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

    __table_args__ = (
        UniqueConstraint("name", "module_name", name="uix_name_module_name_stack"),
    )


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

    __table_args__ = (
        UniqueConstraint("name", "module_name", name="uix_name_module_name_queue"),
    )


class CollectionBase(ResourceContainerBase):
    """
    Base class for collection resources with methods to insert and retrieve assets.

    Attributes:
        contents (Dict[str, Any]): Dictionary of assets in the collection, stored as JSONB.
    """

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

    def retrieve(self, location: int, session: Session) -> Optional[Dict[str, Any]]:
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
        allocation = (
            session.query(AssetAllocation)
            .filter_by(resource_id=self.id, resource_type="collection", index=location)
            .first()
        )

        if allocation:
            asset = session.get(Asset, allocation.asset_id)
            module_name = asset.module_name
            if asset:
                # Deallocate the asset from the collection
                asset.deallocate(session)
                # Update the quantity after removing the asset, ensuring it does not drop below 0
                contents = self.get_contents(session)
                self.quantity = max(len(contents) - 1, 0)  # Prevent negative quantity
                self.save(session)

                return {
                    "id": asset.id,
                    "name": asset.name,
                    "module_name": module_name,
                    "resource_type": "collection",
                    "location": location,
                }
            else:
                raise ValueError(
                    f"Asset with id '{allocation.asset_id}' not found in database."
                )
        else:
            raise ValueError(
                f"Location {location} not found in collection {self.name}."
            )


class Collection(CollectionBase, table=True):
    """
    Table for storing collection resources.

    Attributes:
        assets (List["Asset"]): Relationship to the Asset.
    """

    __table_args__ = (
        UniqueConstraint("name", "module_name", name="uix_name_module_name_collection"),
    )


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
        return self.get_contents(session)  # Since Plate is a collection, we reuse this

    def set_wells(self, wells_dict: Dict[str, float], session: Session):
        """
        Dynamically add or update wells in the plate using well_id and quantity.
        Wells are stored as Pool resources.

        Args:
            wells_dict (Dict[str, float]): A dictionary of well IDs and quantities.
            session (Session): SQLAlchemy session passed from the interface layer.
        """
        current_wells = self.get_wells(session)

        for well_id, quantity in wells_dict.items():
            if well_id in current_wells:
                # Update existing well
                current_wells[well_id].quantity = quantity
            else:
                # Create a new well
                new_well = Pool(
                    description=f"Well {well_id}",
                    name=f"{well_id}",
                    capacity=self.well_capacity,
                    quantity=quantity,
                    module_name=self.name,  # Bug with self.name & self.module_name
                )
                asset = Asset(
                    name=f"{new_well.name}",
                    id=new_well.id,
                    module_name=new_well.module_name,
                )
                session.add(new_well)  # Add the new well to the session
                session.add(asset)
                session.commit()  # Commit to generate the new_well ID

                # Insert the well into the plate's collection resource (indexed by well_id)
                self.insert(location=str(well_id), asset=asset, session=session)

        # Update the plate's total quantity (number of wells)
        self.quantity = len(self.get_wells(session))
        session.commit()
        session.refresh(self)

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
        wells = self.get_wells(session)

        # Check if the well exists
        if well_id in wells:
            well = wells[well_id]
            well.increase(quantity, session)  # Use Pool's increase method
        else:
            raise ValueError(f"Well {well_id} does not exist in plate {self.name}.")

        # Update the total quantity of the plate (number of wells)
        self.quantity = len(self.get_wells(session))
        session.commit()
        session.refresh(self)

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
        wells = self.get_wells(session)

        # Check if the well exists
        if well_id in wells:
            well = wells[well_id]
            well.decrease(quantity, session)  # Use Pool's decrease method
        else:
            raise ValueError(f"Well {well_id} does not exist in plate {self.name}.")

        # Update the total quantity of the plate (number of wells)
        self.quantity = len(self.get_wells(session))
        session.commit()
        session.refresh(self)


# class PlateTable(PlateBase, table=True):
#     """
#     Table for storing plate resources.

#     Attributes:
#         assets (List["Asset"]): Relationship to the Asset.
#     """

#     __table_args__ = (
#         UniqueConstraint("name", "module_name", name="uix_name_module_name_plate"),
#     )
