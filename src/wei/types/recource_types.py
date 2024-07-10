"""Recource Data Classes"""

import random
from typing import Any, Dict, List

import ulid
from pydantic import BaseModel, Field


class Asset(BaseModel):
    """
    Represents an asset (microplate) used for bio/chemistry experiments.

    Attributes:
        id (str): Unique identifier for the asset.
        name (str): Name of the asset.
    """

    id: str = Field(default_factory=lambda: str(ulid.new()))
    name: str

    class Config:
        """Make sure the dataclass is set to allow extra fields with Pydantic"""

        extra = "allow"


class ResourceContainer(BaseModel):
    """
    Base class for all resource containers.

    Attributes:
        information (str): Information about the resource.
        name (str): Name of the resource.
        capacity (float): Capacity of the resource.
        quantity (float): Current quantity of the resource.
    """

    information: str
    name: str
    capacity: float
    quantity: float = 0.0

    def __init__(self, **data: Any):
        """Constructor of the Resource Container"""
        super().__init__(**data)
        if self.quantity > 0 and not data.get("contents"):
            self.initialize_contents()

    def initialize_contents(self):
        """
        Initialize contents with random values. This method should be overridden by subclasses.
        """
        pass

    class Config:
        """Make sure the dataclass is set to allow extra fields with Pydantic"""

        extra = "allow"


class Pool(ResourceContainer):
    """
    Class representing a continuous pool resource.

    Methods:
        increase(amount: float): Increases the quantity by a specified amount.
        decrease(amount: float): Decreases the quantity by a specified amount.
        empty(): Empties the pool.
        fill(): Fills the pool to its capacity.
    """

    contents: List[float] = Field(
        default_factory=list
    )  # No need for initial content with random values
    # We also need collection of pool like to stroe multiple liquid types
    # Weel in a plate would be collection of pools

    def initialize_contents(self):
        """
        Initialize contents with random float values.
        """
        self.contents = [random.uniform(0, 1) for _ in range(int(self.quantity))]

    def increase(self, amount: float) -> None:
        """
        Increases the quantity by a specified amount.

        Args:
            amount (float): The amount to increase.

        Raises:
            ValueError: If the increase exceeds the capacity.
        """
        if self.quantity + amount <= self.capacity:
            self.quantity += amount
        else:
            raise ValueError("Exceeds capacity.")

    def decrease(self, amount: float) -> None:
        """
        Decreases the quantity by a specified amount.

        Args:
            amount (float): The amount to decrease.

        Raises:
            ValueError: If the decrease results in a quantity below zero.
        """
        if self.quantity - amount >= 0:
            self.quantity -= amount
        else:
            raise ValueError("Cannot decrease quantity below zero.")

    def empty(self) -> None:
        """
        Empty by setting the quantity to zero.
        """
        self.quantity = 0.0

    def fill(self) -> None:
        """
        Sets the quantity to its capacity.
        """
        self.quantity = self.capacity
        self.contents = [random.uniform(0, 1) for _ in range(int(self.capacity))]


class CollectionPool(ResourceContainer):
    """Collection pool"""

    pass


class StackQueue(ResourceContainer):
    """
    Class representing a stack or queue resource.

    Attributes:
        contents (List[Any]): List of items in the stack/queue.

    Methods:
        push(instance: Any): Adds an instance to the stack/queue.
        pop(): Removes and returns the last instance from the stack/queue.
        contents(): Returns the contents of the stack/queue.
    """

    contents: List[Asset] = Field(default_factory=list)

    def initialize_contents(self):
        """
        Initialize contents with default assets.
        """
        self.contents = [Asset(name=f"Plate{i+1}") for i in range(int(self.quantity))]

    def push(self, instance: Any) -> int:
        """
        Adds an instance to the stack/queue.

        Args:
            instance (Any): The instance to add.

        Returns:
            int: The position of the instance in the stack/queue.

        Raises:
            ValueError: If the stack/queue is full.
        """
        if len(self.contents) < int(self.capacity):
            self.contents.append(instance)
            self.quantity += 1
        else:
            raise ValueError("Stack/Queue is full.")

    def pop(self) -> Any:
        """
        Removes and returns the last instance from the stack/queue.

        Returns:
            Any: The last instance in the stack/queue.

        Raises:
            ValueError: If the stack/queue is empty.
        """
        if self.contents:
            self.quantity -= 1
            return self.contents.pop()
        else:
            raise ValueError("Stack/Queue is empty.")

    def contents(self) -> List[Any]:
        """
        Returns the contents of the stack/queue.

        Returns:
            List[Any]: The contents of the stack/queue.
        """
        return self.contents


class Collection(ResourceContainer):
    """
    Class representing a collection resource.

    Attributes:
        contents (Dict[str, Any]): Dictionary of items in the collection.

    Methods:
        insert(location: str, instance: Any): Inserts an instance at a specific location.
        retrieve(location: str): Removes and returns the instance from a specific location.
    """

    contents: Dict[str, Any] = Field(default_factory=dict)

    def initialize_contents(self):
        """
        Initialize contents with random values.
        """
        self.contents = {
            f"location_{i+1}": f"random_item_{i+1}" for i in range(int(self.quantity))
        }

    def insert(self, location: str, instance: Any) -> None:
        """
        Inserts an instance at a specific location.

        Args:
            location (str): The location to insert the instance.
            instance (Any): The instance to insert.

        Raises:
            ValueError: If the collection is full.
        """
        if len(self.contents) < int(self.capacity):
            self.contents[location] = instance
            self.quantity += 1
        else:
            raise ValueError("Collection is full.")

    def retrieve(self, location: str = None, value: str = None) -> Any:
        """
        Removes and returns the instance from a specific location.

        Args:
            location (str): The location of the instance to retrieve.

        Returns:
            Any: The instance at the specified location.

        Raises:
            ValueError: If the location is invalid.
        """
        if value and value in self.contents:
            pass
        if location and location in self.contents:
            self.quantity -= 1
            return self.contents.pop(location)
        else:
            raise ValueError("Invalid location.")
