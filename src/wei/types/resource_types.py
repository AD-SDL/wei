"""Resources dataclasses in SQLModel"""

from typing import Dict, List, Optional

import ulid
from sqlalchemy import Column, Text
from sqlmodel import Field, Relationship, SQLModel


class AssetBase(SQLModel):
    """
    Base class for assets with a unique ID and name.

    Attributes:
        id (str): Unique identifier for the asset.
        name (str): Name of the asset.
    """

    id: str = Field(default_factory=lambda: str(ulid.new()), primary_key=True)
    name: str = Field(default="", index=True)


class AssetTable(AssetBase, table=True):
    """
    Table for storing assets.

    Attributes:
        stack_resource_id (Optional[str]): Foreign key to the stack resource.
        queue_resource_id (Optional[str]): Foreign key to the queue resource.
        pool_id (Optional[str]): Foreign key to the pool.
        collection_id (Optional[str]): Foreign key to the collection.
        plate_id (Optional[str]): Foreign key to the plate.
        stack_resource (Optional["Stack"]): Relationship to Stack.
        queue_resource (Optional["Queue"]): Relationship to Queue.
        pool (Optional["Pool"]): Relationship to Pool.
        collection (Optional["Collection"]): Relationship to Collection.
        plate (Optional["Plate"]): Relationship to Plate.
    """

    stack_resource_id: Optional[str] = Field(default=None, foreign_key="stack.id")
    stack_resource: Optional["Stack"] = Relationship(back_populates="assets")

    queue_resource_id: Optional[str] = Field(default=None, foreign_key="queue.id")
    queue_resource: Optional["Queue"] = Relationship(back_populates="assets")

    pool_id: Optional[str] = Field(default=None, foreign_key="pool.id")
    pool: Optional["Pool"] = Relationship(back_populates="assets")

    collection_id: Optional[str] = Field(default=None, foreign_key="collection.id")
    collection: Optional["Collection"] = Relationship(back_populates="assets")

    plate_id: Optional[str] = Field(default=None, foreign_key="plate.id")
    plate: Optional["Plate"] = Relationship(back_populates="assets")


class ResourceContainerBase(AssetBase):
    """
    Base class for resource containers.

    Attributes:
        description (str): Information about the resource.
        capacity (Optional[float]): Capacity of the resource.
    """

    description: str = Field(default="")
    capacity: Optional[float] = Field(default=None, nullable=True)


class Pool(ResourceContainerBase, table=True):
    """
    Table for storing pool resources.

    Attributes:
        quantity (float): Current quantity of the resource.
        assets (List[AssetTable]): Relationship to AssetTable.
    """

    quantity: float = Field(default=0.0)
    assets: List[AssetTable] = Relationship(back_populates="pool")

    def increase(self, amount: float) -> None:
        """
        Increase the quantity by a specified amount.

        Args:
            amount (float): The amount to increase.

        Raises:
            ValueError: If the increase exceeds the capacity.
        """
        if not self.capacity or self.quantity + amount <= self.capacity:
            self.quantity += amount
        else:
            raise ValueError("Exceeds capacity.")

    def decrease(self, amount: float) -> None:
        """
        Decrease the quantity by a specified amount.

        Args:
            amount (float): The amount to decrease.

        Raises:
            ValueError: If the decrease results in a quantity below zero.
        """
        if not self.capacity or self.quantity - amount >= 0:
            self.quantity -= amount
        else:
            raise ValueError("Cannot decrease quantity below zero.")

    def empty(self) -> None:
        """Empty the pool by setting the quantity to zero."""
        self.quantity = 0.0

    def fill(self) -> None:
        """
        Fill the pool to its capacity.

        Raises:
            ValueError: If the capacity is not defined.
        """
        if self.capacity:
            self.quantity = self.capacity
        else:
            raise ValueError("Cannot fill without a defined capacity.")


class Stack(ResourceContainerBase, table=True):
    """
    Table for storing stack resources.

    Attributes:
        contents (List[str]): List of asset IDs in the stack.
        assets (List[AssetTable]): Relationship to AssetTable.
    """

    contents: List[str] = Field(
        default_factory=list, sa_column=Column(Text, nullable=False)
    )
    assets: List[AssetTable] = Relationship(back_populates="stack")

    def push(self, asset_id: str) -> None:
        """
        Add an asset to the stack.

        Args:
            asset_id (str): The ID of the asset to add.

        Raises:
            ValueError: If the stack is full.
        """
        if not self.capacity or len(self.contents) < self.capacity:
            self.contents.append(asset_id)
            self.contents = self.contents  # Ensure SQLModel recognizes the change
        else:
            raise ValueError("Stack is full.")

    def pop(self) -> Optional[str]:
        """
        Remove and return the last asset from the stack.

        Returns:
            str: The ID of the removed asset.

        Raises:
            ValueError: If the stack is empty.
        """
        if self.contents:
            asset_id = self.contents.pop()
            self.contents = self.contents  # Ensure SQLModel recognizes the change
            return asset_id
        else:
            raise ValueError("Stack is empty.")


class Queue(ResourceContainerBase, table=True):
    """
    Table for storing queue resources.

    Attributes:
        contents (List[str]): List of asset IDs in the queue.
        assets (List[AssetTable]): Relationship to AssetTable.
    """

    contents: List[str] = Field(
        default_factory=list, sa_column=Column(Text, nullable=False)
    )
    assets: List[AssetTable] = Relationship(back_populates="queue")

    def push(self, asset_id: str) -> None:
        """
        Add an asset to the queue.

        Args:
            asset_id (str): The ID of the asset to add.

        Raises:
            ValueError: If the queue is full.
        """
        if not self.capacity or len(self.contents) < self.capacity:
            self.contents.append(asset_id)
            self.contents = self.contents  # Ensure SQLModel recognizes the change
        else:
            raise ValueError("Queue is full.")

    def pop(self) -> Optional[str]:
        """
        Remove and return the first asset from the queue.

        Returns:
            str: The ID of the removed asset.

        Raises:
            ValueError: If the queue is empty.
        """
        if self.contents:
            asset_id = self.contents.pop(0)
            self.contents = self.contents  # Ensure SQLModel recognizes the change
            return asset_id
        else:
            raise ValueError("Queue is empty.")


class Collection(ResourceContainerBase, table=True):
    """
    Table for storing collections.

    Attributes:
        contents (Dict[str, str]): Dictionary of location to asset ID.
        assets (List[AssetTable]): Relationship to AssetTable.
    """

    contents: Dict[str, str] = Field(
        default_factory=dict, sa_column=Column(Text, nullable=False)
    )
    assets: List[AssetTable] = Relationship(back_populates="collection")

    def insert(self, location: str, asset_id: str) -> None:
        """
        Insert an asset into the collection at a specific location.

        Args:
            location (str): The location to insert the asset.
            asset_id (str): The ID of the asset to insert.

        Raises:
            ValueError: If the collection is full.
        """
        if len(self.contents) < self.capacity:
            self.contents[location] = asset_id
            self.contents = self.contents  # Ensure SQLModel recognizes the change
        else:
            raise ValueError("Collection is full.")

    def retrieve(self, location: str) -> Optional[str]:
        """
        Remove and return an asset from a specific location in the collection.

        Args:
            location (str): The location of the asset to retrieve.

        Returns:
            str: The ID of the retrieved asset.

        Raises:
            ValueError: If the location is invalid.
        """
        if location in self.contents:
            asset_id = self.contents.pop(location)
            self.contents = self.contents  # Ensure SQLModel recognizes the change
            return asset_id
        else:
            raise ValueError("Invalid location.")


class Plate(ResourceContainerBase, table=True):
    """
    Table for storing multi-welled plates.

    Attributes:
        contents (Dict[str, str]): Dictionary of well ID to asset ID.
        well_capacity (Optional[float]): Capacity of each well.
        assets (List[AssetTable]): Relationship to AssetTable.
    """

    contents: Dict[str, str] = Field(
        default_factory=dict, sa_column=Column(Text, nullable=False)
    )
    well_capacity: Optional[float] = Field(default=None)
    assets: List[AssetTable] = Relationship(back_populates="plate")

    def update_plate(self, new_contents: Dict[str, float]) -> None:
        """
        Update the contents of the plate.

        Args:
            new_contents (Dict[str, float]): The new contents to update.
        """
        for well_id, quantity in new_contents.items():
            if well_id in self.contents:
                self.contents[well_id] = quantity
            else:
                self.contents[well_id] = Pool(
                    description=f"Well {well_id}",
                    name=f"Well{well_id}",
                    capacity=self.well_capacity,
                    quantity=quantity,
                ).id
        self.contents = self.contents  # Ensure SQLModel recognizes the change
