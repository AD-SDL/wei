"""Resources Data Classes"""

import copy
from typing import Any, Dict, List, Optional

import ulid
from sqlalchemy import Column, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field as SQLField
from sqlmodel import Relationship, Session, SQLModel


class AssetBase(SQLModel):
    """
    Base class for assets with an ID and a name.

    Attributes:
        id (str): Unique identifier for the asset.
        name (str): Name of the asset.
    """

    id: str = SQLField(default_factory=lambda: str(ulid.new()), primary_key=True)
    name: str = SQLField(default="", nullable=False)
    module_name: str = SQLField(default="", nullable=False)


class AssetTable(AssetBase, table=True):
    """
    Represents the asset table with relationships to other resources.

    Attributes:
        stack_resource_id (Optional[str]): Foreign key to the stack table.
        queue_resource_id (Optional[str]): Foreign key to the queue table.
        pool_id (Optional[str]): Foreign key to the pool table.
        collection_id (Optional[str]): Foreign key to the collection table.
        plate_id (Optional[str]): Foreign key to the plate table.
        stack (Optional["StackTable"]): Relationship to the StackTable.
        queue (Optional["QueueTable"]): Relationship to the QueueTable.
        pool (Optional["PoolTable"]): Relationship to the PoolTable.
        collection (Optional["CollectionTable"]): Relationship to the CollectionTable.
        plate (Optional["PlateTable"]): Relationship to the PlateTable.
    """

    stack_resource_id: Optional[str] = SQLField(
        default=None, foreign_key="stacktable.id", nullable=True
    )
    queue_resource_id: Optional[str] = SQLField(
        default=None, foreign_key="queuetable.id", nullable=True
    )
    pool_id: Optional[str] = SQLField(
        default=None, foreign_key="pooltable.id", nullable=True
    )
    collection_id: Optional[str] = SQLField(
        default=None, foreign_key="collectiontable.id", nullable=True
    )
    plate_id: Optional[str] = SQLField(
        default=None, foreign_key="platetable.id", nullable=True
    )

    stack: Optional["StackTable"] = Relationship(back_populates="assets")
    queue: Optional["QueueTable"] = Relationship(back_populates="assets")
    pool: Optional["PoolTable"] = Relationship(back_populates="assets")
    collection: Optional["CollectionTable"] = Relationship(back_populates="assets")
    plate: Optional["PlateTable"] = Relationship(back_populates="assets")

    def __repr__(self):
        """
        Returns a string representation of the asset, including its relationships.

        Returns:
            str: String representation of the asset.
        """
        attrs = [f"id='{self.id}'", f"name='{self.name}'"]

        if self.stack_resource_id:
            attrs.append(
                f"stack_resource_id='{self.stack_resource_id}', stack_content='{self.stack.contents}'"
            )
        if self.pool_id:
            attrs.append(
                f"pool_id='{self.pool_id}', pool_content='{self.pool.quantity}'"
            )
        if self.queue_resource_id:
            attrs.append(
                f"queue_resource_id='{self.queue_resource_id}', queue_content='{self.queue.contents}'"
            )
        if self.collection_id:
            attrs.append(
                f"collection_id='{self.collection_id}', collection_content='{self.collection.contents}'"
            )
        if self.plate_id:
            attrs.append(
                f"plate_id='{self.plate_id}', plate_content='{self.plate.contents}'"
            )

        return f"({', '.join(attrs)})"

    def allocate_to_resource(
        self, resource_type: str, resource_id: str, session: Session
    ):
        """
        Allocate this asset to a specific resource.

        Args:
            resource_type (str): The type of the resource ('stack', 'queue', etc.).
            resource_id (str): The ID of the resource.
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
            ):
                # The asset is already allocated to this resource, no need to do anything.
                return
            else:
                # The asset is already allocated to a different resource.
                raise ValueError(
                    f"Asset {self.id} is already allocated to a different resource."
                )

        # If no existing allocation, create a new one
        new_allocation = AssetAllocation(
            asset_id=self.id, resource_type=resource_type, resource_id=resource_id
        )
        session.add(new_allocation)
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

        session.delete(allocation)
        session.commit()

    @staticmethod
    def handle_asset_deletion(session: Session):
        """
        Trigger function to remove an asset from a resource's contents when the asset is deleted.

        Args:
            session (Session): SQLAlchemy session to use for handling the deletion.
        """
        # Implementation depends on setting up triggers in your PostgreSQL database.
        pass


class AssetAllocation(SQLModel, table=True):
    """
    Table that tracks which asset is allocated to which resource.

    Attributes:
        asset_id (str): Foreign key referencing the AssetTable.
        resource_type (str): Type of resource (e.g., 'stack', 'queue').
        resource_id (str): ID of the resource to which the asset is allocated.
    """

    asset_id: str = SQLField(
        primary_key=True, foreign_key="assettable.id", nullable=False
    )
    resource_type: str = SQLField(nullable=False)
    resource_id: str = SQLField(nullable=False)


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


class PoolTable(PoolBase, table=True):
    """
    Table for storing pool resources.

    Attributes:
        assets (List["AssetTable"]): Relationship to the AssetTable.
    """

    assets: List["AssetTable"] = Relationship(back_populates="pool")

    __table_args__ = (
        UniqueConstraint("name", "module_name", name="uix_name_module_name_pool"),
    )


class StackBase(ResourceContainerBase):
    """
    Base class for stack resources with methods to push and pop assets.

    Attributes:
        contents (List[Dict[str, Any]]): List of assets in the stack, stored as JSONB.
    """

    contents: List[Dict[str, Any]] = SQLField(
        sa_column=Column("contents", JSONB, default=list)
    )

    @property
    def contents_list(self) -> List[Dict[str, Any]]:
        """
        Return a deep copy of the stack's contents.

        Returns:
            List[Dict[str, Any]]: The contents of the stack.
        """
        return copy.deepcopy(self.contents)

    def push(self, instance: AssetTable, session: Session) -> int:
        """
        Return a deep copy of the stack's contents.

        Returns:
            List[Dict[str, Any]]: The contents of the stack.
        """
        contents = self.contents_list

        if not self.capacity or len(contents) < int(self.capacity):
            serialized_instance = {"id": instance.id, "name": instance.name}
            contents.append(serialized_instance)
            self.contents = contents  # Ensure reassignment to the model attribute
            self.quantity = len(contents)
            self.save(session)
            session.commit()  # Explicitly commit the session
            instance.allocate_to_resource("stack", self.id, session)
        else:
            raise ValueError(f"Resource {self.name} is full.")

        return len(contents) - 1

    def pop(self, session: Session) -> Any:
        """
        Pop the last asset from the stack.

        Args:
            session (Session): SQLAlchemy session to use for saving.

        Returns:
            Any: The popped asset.

        Raises:
            ValueError: If the stack is empty or if the asset is not found.
        """
        contents = self.contents_list

        if contents:
            instance_data = contents.pop()
            self.contents = contents
            self.quantity = len(contents)
            self.save(session)
            session.commit()  # Explicitly commit the session

            instance = session.get(AssetTable, instance_data["id"])
            if instance:
                instance.deallocate(session)  # Deallocate asset from this stack
                return instance
            else:
                raise ValueError(f"Asset with id '{instance_data['id']}' not found.")
        else:
            raise ValueError(f"Resource {self.name} is empty.")


class StackTable(StackBase, table=True):
    """
    Table for storing stack resources.

    Attributes:
        assets (List["AssetTable"]): Relationship to the AssetTable.
    """

    assets: List["AssetTable"] = Relationship(back_populates="stack")
    __table_args__ = (
        UniqueConstraint("name", "module_name", name="uix_name_module_name_stack"),
    )


class QueueBase(ResourceContainerBase):
    """
    Base class for queue resources with methods to push and pop assets.

    Attributes:
        contents (List[Dict[str, Any]]): List of assets in the queue, stored as JSONB.
    """

    contents: List[Dict[str, Any]] = SQLField(
        sa_column=Column("contents", JSONB, default=list)
    )

    @property
    def contents_list(self) -> List[Dict[str, Any]]:
        """
        Return a deep copy of the queue's contents.

        Returns:
            List[Dict[str, Any]]: The contents of the queue.
        """
        return copy.deepcopy(self.contents)

    def push(self, instance: Any, session: Session) -> int:
        """
        Push a new asset onto the queue.

        Args:
            instance (Any): The asset to push onto the queue.
            session (Session): SQLAlchemy session to use for saving.

        Returns:
            int: The index of the pushed asset.

        Raises:
            ValueError: If the queue is full.
        """
        contents = self.contents_list

        if not self.capacity or self.quantity < int(self.capacity):
            serialized_instance = {"id": instance.id, "name": instance.name}
            contents.append(serialized_instance)
            self.contents = contents  # Ensure reassignment to the model attribute
            self.quantity = len(contents)
            self.save(session)
            session.commit()  # Explicitly commit the session
            # Allocate asset to this queue
            instance.allocate_to_resource("queue", self.id, session)
        else:
            raise ValueError(f"Resource {self.name} is full.")

        return len(contents) - 1

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
        contents = self.contents_list

        if contents:
            instance_data = contents.pop(0)  # Queue uses FIFO, so pop from the front
            self.contents = contents
            self.quantity = len(contents)
            self.save(session)
            session.commit()  # Explicitly commit the session
            instance = session.get(AssetTable, instance_data["id"])
            if instance:
                instance.deallocate(session)
                return instance
            else:
                raise ValueError(f"Asset with id '{instance_data['id']}' not found.")
        else:
            raise ValueError(f"Resource {self.name} is empty.")


class QueueTable(QueueBase, table=True):
    """
    Table for storing queue resources.

    Attributes:
        assets (List["AssetTable"]): Relationship to the AssetTable.
    """

    assets: List["AssetTable"] = Relationship(back_populates="queue")
    __table_args__ = (
        UniqueConstraint("name", "module_name", name="uix_name_module_name_queue"),
    )


class CollectionBase(ResourceContainerBase):
    """
    Base class for collection resources with methods to insert and retrieve assets.

    Attributes:
        contents (Dict[str, Any]): Dictionary of assets in the collection, stored as JSONB.
    """

    contents: Dict[str, Any] = SQLField(
        sa_column=Column("contents", JSONB, default=dict)
    )

    @property
    def contents_dict(self) -> Dict[str, AssetBase]:
        """
        Return a dictionary of the collection's contents.

        Returns:
            Dict[str, AssetBase]: The contents of the collection.
        """
        return {k: AssetBase(**v) for k, v in self.contents.items()}

    def insert(self, location: str, asset: AssetTable, session: Session) -> None:
        """
        Insert a new asset into the collection at the specified location.

        Args:
            location (str): The location in the collection to insert the asset.
            asset (AssetTable): The asset to insert.
            session (Session): SQLAlchemy session to use for saving.

        Raises:
            ValueError: If the collection is full.
        """
        contents = self.contents_dict
        if self.quantity < int(self.capacity):
            serialized_asset = {"id": asset.id, "name": asset.name}
            contents[location] = serialized_asset
            self.contents = contents
            self.quantity = len(contents)
            self.save(session)
            # Allocate asset to this collection
            asset.allocate_to_resource("collection", self.id, session)
        else:
            raise ValueError("Collection is full.")

    def retrieve(self, location: str, session: Session) -> Optional[Dict[str, Any]]:
        """
        Retrieve an asset from the collection at the specified location.

        Args:
            location (str): The location in the collection to retrieve the asset from.
            session (Session): SQLAlchemy session to use for fetching and saving.

        Returns:
            Optional[Dict[str, Any]]: The retrieved asset data.

        Raises:
            ValueError: If the location is invalid or the asset is not found.
        """
        contents = self.contents_dict
        if location in contents:
            asset_data = contents.pop(location)
            self.contents = contents
            self.quantity = len(contents)
            self.save(session)

            asset = session.get(AssetTable, asset_data.id)
            if asset:
                asset.deallocate(session)
                return {"id": asset.id, "name": asset.name}
            else:
                raise ValueError(
                    f"Asset with id '{asset_data.id}' not found in the database."
                )
        else:
            raise ValueError(f"Invalid location: {location} not found in collection.")


class CollectionTable(CollectionBase, table=True):
    """
    Table for storing collection resources.

    Attributes:
        assets (List["AssetTable"]): Relationship to the AssetTable.
    """

    assets: List["AssetTable"] = Relationship(back_populates="collection")

    __table_args__ = (
        UniqueConstraint("name", "module_name", name="uix_name_module_name_collection"),
    )


class PlateBase(ResourceContainerBase):
    """
    Base class for plate resources with methods to manage wells.

    Attributes:
        contents (Dict[str, Any]): Dictionary of wells in the plate, stored as JSONB.
        well_capacity (Optional[float]): Capacity of each well in the plate.
    """

    contents: Dict[str, Any] = SQLField(
        sa_column=Column("contents", JSONB, default=dict)
    )
    well_capacity: Optional[float] = None

    @property
    def wells(self) -> Dict[str, PoolTable]:
        """
        Return a dictionary of wells in the plate.

        Returns:
            Dict[str, PoolTable]: The wells in the plate.
        """
        return {k: PoolTable(**v) for k, v in self.contents.items()}

    @wells.setter
    def wells(self, value: Dict[str, PoolTable]):
        """
        Set the wells in the plate.

        Args:
            value (Dict[str, PoolTable]): The new wells to set in the plate.
        """
        self.contents = {k: v.model_dump() for k, v in value.items()}

    def update_plate(self, new_contents: Dict[str, float], session: Session):
        """
        Update the plate with new contents.

        Args:
            new_contents (Dict[str, float]): The new contents for the wells.
            session (Session): SQLAlchemy session to use for saving.
        """

        wells = self.wells
        for well_id, quantity in new_contents.items():
            if well_id in wells:
                wells[well_id].quantity = quantity
            else:
                wells[well_id] = PoolTable(
                    description=f"Well {well_id}",
                    name=f"Well{well_id}",
                    capacity=self.well_capacity,
                    quantity=quantity,
                )
        self.wells = wells
        self.quantity = len(wells)
        self.save(session)

    def update_well(self, well_id: str, quantity: float, session: Session):
        """
        Update a specific well in the plate.

        Args:
            well_id (str): The ID of the well to update.
            quantity (float): The new quantity for the well.
            session (Session): SQLAlchemy session to use for saving.
        """
        wells = self.wells
        if well_id in wells:
            wells[well_id].quantity = quantity
        else:
            wells[well_id] = PoolTable(
                description=f"Well {well_id}",
                name=f"Well{well_id}",
                capacity=self.well_capacity,
                quantity=quantity,
            )
        self.wells = wells
        self.quantity = len(wells)
        self.save(session)


class PlateTable(PlateBase, table=True):
    """
    Table for storing plate resources.

    Attributes:
        assets (List["AssetTable"]): Relationship to the AssetTable.
    """

    assets: List["AssetTable"] = Relationship(back_populates="plate")
    __table_args__ = (
        UniqueConstraint("name", "module_name", name="uix_name_module_name_plate"),
    )
