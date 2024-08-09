"""Resources Data Classes"""

import json
from typing import Any, Dict, List, Optional

import ulid
from sqlalchemy import Column, Text
from sqlmodel import Field as SQLField
from sqlmodel import Relationship, Session, SQLModel


class AssetBase(SQLModel):
    """
    Base class for assets with a unique identifier and a name.

    Attributes:
        id (str): The unique identifier for the asset, generated using ULID.
        name (str): The name of the asset.
    """

    id: str = SQLField(default_factory=lambda: str(ulid.new()), primary_key=True)
    name: str = SQLField(default="")


class AssetTable(AssetBase, table=True):
    """
    Represents an asset stored in the database, with potential relationships to various resource types.

    Attributes:
        stack_resource_id (Optional[str]): Foreign key linking to the Stack resource.
        queue_resource_id (Optional[str]): Foreign key linking to the Queue resource.
        pool_id (Optional[str]): Foreign key linking to the Pool resource.
        collection_id (Optional[str]): Foreign key linking to the Collection resource.
        plate_id (Optional[str]): Foreign key linking to the Plate resource.
    """

    stack_resource_id: Optional[str] = SQLField(
        default=None, foreign_key="stacktable.id"
    )
    queue_resource_id: Optional[str] = SQLField(
        default=None, foreign_key="queuetable.id"
    )
    pool_id: Optional[str] = SQLField(default=None, foreign_key="pooltable.id")
    collection_id: Optional[str] = SQLField(
        default=None, foreign_key="collectiontable.id"
    )
    plate_id: Optional[str] = SQLField(default=None, foreign_key="platetable.id")
    stack: Optional["StackTable"] = Relationship(back_populates="assets")
    queue: Optional["QueueTable"] = Relationship(back_populates="assets")
    pool: Optional["PoolTable"] = Relationship(back_populates="assets")
    collection: Optional["CollectionTable"] = Relationship(back_populates="assets")
    plate: Optional["PlateTable"] = Relationship(back_populates="assets")


class ResourceContainerBase(AssetBase):
    """
    Base class for resource containers that can hold assets.

    Attributes:
        description (str): A description of the resource.
        capacity (Optional[float]): The capacity of the resource.
        quantity (float): The current quantity of the resource.
    """

    description: str = SQLField(default="")
    capacity: Optional[float] = SQLField(default=None, nullable=True)
    quantity: float = SQLField(default=0.0)

    def save(self, session: Session):
        """
        Save the current state of the resource container to the database.

        Args:
            session (Session): The SQLAlchemy session used to commit the changes.
        """
        session.add(self)
        session.commit()
        session.refresh(self)


class PoolBase(ResourceContainerBase):
    """
    Base class for a pool resource that can hold a single continuous quantity.

    Methods:
        increase(amount: float, session: Session): Increase the pool's quantity by a specified amount.
        decrease(amount: float, session: Session): Decrease the pool's quantity by a specified amount.
    """

    def increase(self, amount: float, session: Session) -> None:
        """
        Increase the pool's quantity by a specified amount.

        Args:
            amount (float): The amount to increase the pool's quantity by.
            session (Session): The SQLAlchemy session used to commit the changes.

        Raises:
            ValueError: If the increase would exceed the pool's capacity.
        """
        if not self.capacity or self.quantity + amount <= self.capacity:
            self.quantity += amount
            self.save(session)  # Save the updated state to the database
        else:
            raise ValueError("Exceeds capacity.")

    def decrease(self, amount: float, session: Session) -> None:
        """
        Decrease the pool's quantity by a specified amount.

        Args:
            amount (float): The amount to decrease the pool's quantity by.
            session (Session): The SQLAlchemy session used to commit the changes.

        Raises:
            ValueError: If the decrease would result in a negative quantity.
        """
        if not self.capacity or self.quantity - amount >= 0:
            self.quantity -= amount
            self.save(session)  # Save the updated state to the database
        else:
            raise ValueError("Cannot decrease quantity below zero.")

    def empty(self, session: Session) -> None:
        """
        Empty the pool by setting the quantity to zero.
        """
        self.quantity = 0.0
        self.save(session)

    def fill(self, session: Session) -> None:
        """
        Fill the pool by setting the quantity to its capacity.
        """
        if self.capacity:
            self.quantity = self.capacity
            self.save(session)
        else:
            raise ValueError("Cannot fill without a defined capacity.")


class PoolTable(PoolBase, table=True):
    """
    Table representation of a pool resource.
    """

    assets: List["AssetTable"] = Relationship(back_populates="pool")


class StackBase(ResourceContainerBase):
    """
    Base class for a stack resource that can hold multiple assets in a last-in, first-out (LIFO) manner.

    Attributes:
        stack_contents (str): JSON-encoded string representing the contents of the stack.

    Methods:
        push(instance: Any, session: Session): Add an asset to the top of the stack.
        pop(session: Session): Remove and return the asset at the top of the stack.
    """

    stack_contents: str = SQLField(
        sa_column=Column("stack_contents", Text, default="[]")
    )

    @property
    def contents_list(self) -> List[AssetBase]:
        """
        Returns the contents of the stack as a list of assets.

        Returns:
            List[AssetBase]: A list of assets in the stack.
        """
        return [AssetBase(**item) for item in json.loads(self.stack_contents)]

    def push(self, instance: Any, session: Session) -> int:
        """
        Add an asset to the top of the stack.

        Args:
            instance (Any): The asset to add to the stack.
            session (Session): The SQLAlchemy session used to commit the changes.

        Returns:
            int: The new position of the asset in the stack.

        Raises:
            ValueError: If the stack is full.
        """
        contents = self.contents_list
        if not self.capacity or len(contents) < int(self.capacity):
            # Only include the relevant fields when serializing the asset
            serialized_instance = {"id": instance.id, "name": instance.name}
            contents.append(serialized_instance)
            self.stack_contents = json.dumps(contents)
            self.quantity = len(contents)  # Update quantity
            self.save(session)  # Save the updated state to the database
        else:
            raise ValueError(f"Resource {self.name} is full.")
        return len(contents) - 1

    def pop(self, session: Session) -> Any:
        """
        Remove and return the asset at the top of the stack.

        Args:
            session (Session): The SQLAlchemy session used to commit the changes.

        Returns:
            Any: The asset that was at the top of the stack.

        Raises:
            ValueError: If the stack is empty.
        """
        contents = self.contents_list
        if contents:
            instance = contents.pop()
            self.stack_contents = json.dumps(contents)
            self.quantity = len(contents)  # Update quantity
            self.save(session)  # Save the updated state to the database
            return instance
        else:
            raise ValueError(f"Resource {self.name} is empty.")


class StackTable(StackBase, table=True):
    """
    Table representation of a stack resource.
    """

    assets: List["AssetTable"] = Relationship(back_populates="stack")


class QueueBase(ResourceContainerBase):
    """
    Base class for a queue resource that can hold multiple assets in a first-in, first-out (FIFO) manner.

    Attributes:
        queue_contents (str): JSON-encoded string representing the contents of the queue.

    Methods:
        push(instance: Any, session: Session): Add an asset to the end of the queue.
        pop(session: Session): Remove and return the asset at the front of the queue.
    """

    queue_contents: str = SQLField(
        sa_column=Column("queue_contents", Text, default="[]")
    )

    @property
    def contents_list(self) -> List[AssetBase]:
        """
        Returns the contents of the queue as a list of assets.

        Returns:
            List[AssetBase]: A list of assets in the queue.
        """
        return [AssetBase(**item) for item in json.loads(self.queue_contents)]

    def push(self, instance: Any, session: Session) -> int:
        """
        Add an asset to the end of the queue.

        Args:
            instance (Any): The asset to add to the queue.
            session (Session): The SQLAlchemy session used to commit the changes.

        Returns:
            int: The new position of the asset in the queue.

        Raises:
            ValueError: If the queue is full.
        """
        contents = self.contents_list
        if not self.capacity or self.quantity < int(self.capacity):
            # Only include the relevant fields when serializing the asset
            serialized_instance = {"id": instance.id, "name": instance.name}
            contents.append(serialized_instance)
            self.queue_contents = json.dumps(contents)
            self.quantity = len(contents)  # Update quantity
            self.save(session)  # Save the updated state to the database
        else:
            raise ValueError(f"Resource {self.name} is full.")
        return len(contents) - 1

    def pop(self, session: Session) -> Any:
        """
        Remove and return the asset at the front of the queue.

        Args:
            session (Session): The SQLAlchemy session used to commit the changes.

        Returns:
            Any: The asset that was at the front of the queue.

        Raises:
            ValueError: If the queue is empty.
        """
        contents = self.contents_list
        if contents:
            instance = contents.pop(0)
            self.queue_contents = json.dumps(contents)
            self.quantity = len(contents)  # Update quantity
            self.save(session)  # Save the updated state to the database
            return instance
        else:
            raise ValueError(f"Resource {self.name} is empty.")


class QueueTable(QueueBase, table=True):
    """
    Table representation of a queue resource.
    """

    assets: List["AssetTable"] = Relationship(back_populates="queue")


class CollectionBase(ResourceContainerBase):
    """
    Base class for a collection resource that allows random access to assets.

    Attributes:
        collection_contents (str): JSON-encoded string representing the contents of the collection.
    """

    collection_contents: str = SQLField(
        sa_column=Column("collection_contents", Text, default="{}")
    )

    @property
    def contents_dict(self) -> Dict[str, AssetBase]:
        """
        Returns the contents of the collection as a dictionary of assets.

        Returns:
            Dict[str, AssetBase]: A dictionary of assets in the collection.
        """
        return {
            k: AssetBase(**v) for k, v in json.loads(self.collection_contents).items()
        }

    def insert(self, location: str, asset: AssetTable, session: Session) -> None:
        """
        Insert an asset at a specified location in the collection.

        Args:
            location (str): The location to insert the asset.
            asset (AssetTable): The asset to insert.
            session (Session): The SQLAlchemy session used to commit the changes.

        Raises:
            ValueError: If the collection is full.
        """
        contents = self.contents_dict
        if self.quantity < int(self.capacity):
            # Only include the relevant fields when serializing the asset
            serialized_asset = {"id": asset.id, "name": asset.name}
            contents[location] = serialized_asset
            self.collection_contents = json.dumps(contents)
            self.quantity = len(contents)  # Update quantity
            self.save(session)  # Save the updated state to the database
        else:
            raise ValueError("Collection is full.")

    def retrieve(self, location: str, session: Session) -> Optional[Dict[str, Any]]:
        """
        Retrieve and remove an asset from a specified location in the collection.

        Args:
            location (str): The location of the asset to retrieve.
            session (Session): The SQLAlchemy session used to commit the changes.

        Returns:
            Optional[Dict[str, Any]]: A dictionary containing the retrieved asset's id and name, or None if not found.

        Raises:
            ValueError: If the location is invalid.
        """
        contents = self.contents_dict
        if location in contents:
            asset_data = contents.pop(location)
            # print(f"Debug: Asset data retrieved for location '{location}': {asset_data}")  # Debug line

            self.collection_contents = json.dumps(contents)
            self.quantity = len(contents)  # Update quantity
            self.save(session)  # Save the updated state to the database

            # Directly access the id and name attributes of asset_data
            asset = session.get(AssetTable, asset_data.id)
            if not asset:
                raise ValueError(
                    f"Asset with id '{asset_data.id}' not found in the database."
                )

            # Return only the id and name in a dictionary format
            return {"id": asset.id, "name": asset.name}
        else:
            raise ValueError(f"Invalid location: {location} not found in collection.")


class CollectionTable(CollectionBase, table=True):
    """
    Table representation of a collection resource.
    """

    assets: List["AssetTable"] = Relationship(back_populates="collection")


class PlateBase(ResourceContainerBase):
    """
    Base class for a multi-well plate resource that holds multiple pools.

    Attributes:
        plate_contents (str): JSON-encoded string representing the contents of the plate.
        well_capacity (Optional[float]): The capacity of each well in the plate.

    Methods:
        update_plate(new_contents: Dict[str, float], session: Session): Update the contents of the entire plate.
        update_well(well_id: str, quantity: float, session: Session): Update the quantity in a specific well.
    """

    plate_contents: str = SQLField(
        sa_column=Column("plate_contents", Text, default="{}")
    )
    well_capacity: Optional[float] = None

    @property
    def wells(self) -> Dict[str, PoolTable]:
        """
        Returns the contents of the plate as a dictionary of wells (each well being a pool).

        Returns:
            Dict[str, PoolTable]: A dictionary of pools representing the wells.
        """
        return {k: PoolTable(**v) for k, v in json.loads(self.plate_contents).items()}

    @wells.setter
    def wells(self, value: Dict[str, PoolTable]):
        """
        Sets the contents of the plate using a dictionary of wells.

        Args:
            value (Dict[str, PoolTable]): The new contents for the plate.
        """
        self.plate_contents = json.dumps({k: v.model_dump() for k, v in value.items()})

    def update_plate(self, new_contents: Dict[str, float], session: Session):
        """
        Update the contents of the entire plate.

        Args:
            new_contents (Dict[str, float]): A dictionary with well IDs as keys and quantities as values.
            session (Session): The SQLAlchemy session used to commit the changes.
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
        self.quantity = len(wells)  # Update the quantity to reflect the number of wells
        self.save(session)  # Save the updated state to the database

    def update_well(self, well_id: str, quantity: float, session: Session):
        """
        Update the quantity in a specific well.

        Args:
            well_id (str): The ID of the well to update.
            quantity (float): The new quantity for the well.
            session (Session): The SQLAlchemy session used to commit the changes.
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
        self.quantity = len(wells)  # Update the quantity to reflect the number of wells
        self.save(session)  # Save the updated state to the database


class PlateTable(PlateBase, table=True):
    """
    Table representation of a multi-well plate resource.
    """

    assets: List["AssetTable"] = Relationship(back_populates="plate")
