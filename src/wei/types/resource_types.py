"""Recource Data Classes"""

from typing import Any, Dict, List, Union

import ulid
from pydantic import BaseModel, Field


class Asset(BaseModel, extra="allow"):
    """
    Represents an asset (microplate) used for bio/chemistry experiments.

    Attributes:
        id (str): Unique identifier for the asset.
        name (str): Name of the asset.
    """

    id: str = Field(default_factory=lambda: str(ulid.new()))
    name: str


class ResourceContainer(BaseModel, extra="allow"):
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


class Pool(ResourceContainer):
    """
    Class representing a continuous pool resource.

    Methods:
        increase(amount: float): Increases the quantity by a specified amount.
        decrease(amount: float): Decreases the quantity by a specified amount.
        empty(): Empties the pool.
        fill(): Fills the pool to its capacity.
    """

    contents: Dict[str, Any] = Field(default_factory=dict)

    def initialize_contents(self):
        """
        Initialize contents with default information about the asset.
        """
        self.contents = {"description": self.name, "quantity": self.quantity}

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
            self.contents["quantity"] = self.quantity
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
            self.contents["quantity"] = self.quantity
        else:
            raise ValueError("Cannot decrease quantity below zero.")

    def empty(self) -> None:
        """
        Empty by setting the quantity to zero.
        """
        self.quantity = 0.0
        self.contents["quantity"] = 0.0

    def fill(self) -> None:
        """
        Sets the quantity to its capacity.
        """
        self.quantity = self.capacity
        self.contents["quantity"] = self.capacity


class PoolCollection(BaseModel, extra="allow"):  # Could be renamed with Plate
    """
    Class representing a collection of pools in a plate.

    Attributes:
        id (str): Unique identifier for the plate.
        name (str): Name of the plate.
        wells (List[Pool]): List of pools representing wells in the plate.
    """

    name: str
    wells: Dict[str, Pool] = Field(default_factory=dict)

    def update_well(self, well_id: str, action: str, amount: float = 0.0):
        """Updates specific wells"""
        if well_id in self.wells:
            well = self.wells[well_id]
            if action == "increase":
                well.increase(amount)
            elif action == "decrease":
                well.decrease(amount)
            elif action == "fill":
                well.fill()
            elif action == "empty":
                well.empty()

    def update_plate(self, new_contents: Dict[str, Dict[str, Union[str, float]]]):
        """Updates the whole plate content"""
        for well_id, content in new_contents.items():
            if well_id in self.wells:
                self.wells[well_id].contents = content
                self.wells[well_id].quantity = content.get("quantity", 0.0)
            else:
                self.wells[well_id] = Pool(
                    information=f"Well {well_id}",
                    name=f"Well{well_id}",
                    capacity=100.0,  # Assume a default capacity if not provided
                    quantity=content.get("quantity", 0.0),
                    contents=content,
                )


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
