"""Resource Data Classes"""

from typing import Any, Dict, List, Optional, Union

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
    name: str = ""


class ResourceContainer(Asset):
    """
    Base class for all resource containers.

    Attributes:
        description (str): Information about the resource.
        capacity (Optional[Union[float, int]]): Capacity of the resource.
    """

    description: str = ""
    capacity: Optional[Union[float, int]] = None


class Pool(ResourceContainer):
    """
    Class representing a continuous pool resource containing a single element.

    Attributes:
        quantity (float): Current quantity of the resource.
    """

    quantity: float = 0.0

    def increase(self, amount: float) -> None:
        """
        Increases the quantity by a specified amount.

        Args:
            amount (float): The amount to increase.
        """
        if not self.capacity or self.quantity + amount <= self.capacity:
            self.quantity += amount
        else:
            raise ValueError("Exceeds capacity.")

    def decrease(self, amount: float) -> None:
        """
        Decreases the quantity by a specified amount.

        Args:
            amount (float): The amount to decrease.
        """
        if not self.capacity or self.quantity - amount >= 0:
            self.quantity -= amount
        else:
            raise ValueError("Cannot decrease quantity below zero.")

    def empty(self) -> None:
        """
        Empty the pool by setting the quantity to zero.
        """
        self.quantity = 0.0

    def fill(self) -> None:
        """
        Fill the pool to its capacity.
        """
        if self.capacity:
            self.quantity = self.capacity
        else:
            raise ValueError("Cannot fill without a defined capacity.")


class StackResource(ResourceContainer):
    """
    Class representing a stack resource.

    Attributes:
        contents (List[Asset]): List of items in the stack.
    """

    contents: List[Asset] = Field(default_factory=list)

    @property
    def quantity(self) -> int:
        """Returns the number of assets in the stack resource container"""
        return len(self.contents)

    @quantity.setter
    def quantity(self, value: int):
        """Fill empty stack space with anonymous assets"""
        while len(self.contents) < value:
            self.push(Asset())

    def push(self, instance: Any) -> int:
        """
        Adds an instance to the stack.

        Args:
            instance (Any): The instance to add.

        Returns:
            int: The position of the instance in the stack.
        """
        if not self.capacity or len(self.contents) < int(self.capacity):
            self.contents.append(instance)
        else:
            raise ValueError(f"Resource {self.name} is full.")
        return len(self.contents) - 1

    def pop(self) -> Any:
        """
        Removes and returns the last instance from the stack.

        Returns:
            Any: The last instance in the stack.
        """
        if self.contents:
            return self.contents.pop()
        else:
            raise ValueError(f"Resource {self.name} is empty.")


class QueueResource(ResourceContainer):
    """
    Class representing a queue-style resource.

    Attributes:
        contents (List[Asset]): List of items in the queue.
    """

    contents: List[Asset] = Field(default_factory=list)

    @property
    def quantity(self) -> int:
        """Returns the number of assets in the resource container"""
        return len(self.contents)

    @quantity.setter
    def quantity(self, value: int):
        """Fill empty queue space with anonymous assets"""
        while len(self.contents) < value:
            self.push(Asset())

    def push(self, instance: Any) -> int:
        """
        Adds an instance to the queue.

        Args:
            instance (Any): The instance to add.

        Returns:
            int: The position of the instance in the queue.
        """
        if not self.capacity or self.quantity < int(self.capacity):
            self.contents.append(instance)
        else:
            raise ValueError(f"Resource {self.name} is full.")
        return len(self.contents) - 1

    def pop(self) -> Any:
        """
        Removes and returns the first instance from the queue.

        Returns:
            Any: The first instance in the queue.
        """
        if self.contents:
            return self.contents.pop(0)
        else:
            raise ValueError(f"Resource {self.name} is empty.")


class Collection(ResourceContainer):
    """
    Class representing a resource container that allows random access.

    Attributes:
        contents (Dict[str, Any]): Dictionary of items in the collection.
    """

    contents: Dict[str, Any] = Field(default_factory=dict)

    @property
    def quantity(self) -> int:
        """Returns the number of elements in the collection"""
        return len(self.contents)

    @quantity.setter
    def quantity(self, value: int):
        """Fill empty collection space with anonymous assets"""
        raise ValueError(
            "Collections do not support arbitrarily setting quantity. Please use the `insert` and `remove` methods instead."
        )

    def insert(self, location: str, instance: Any) -> None:
        """
        Inserts an instance at a specific location.

        Args:
            location (str): The location to insert the instance.
            instance (Any): The instance to insert.
        """
        if self.quantity < int(self.capacity):
            self.contents[location] = instance
        else:
            raise ValueError("Collection is full.")

    def retrieve(self, location: str = None) -> Any:
        """
        Removes and returns the instance from a specific location.

        Args:
            location (str): The location of the instance to retrieve.
        """
        if location and location in self.contents:
            return self.contents.pop(location)
        else:
            raise ValueError("Invalid location.")


class Plate(Collection):
    """
    Class representing a multi-welled plate.

    Attributes:
        wells (Dict[str, Pool]): List of pools representing wells in the plate.
        well_capacity (Optional[float]): Capacity of each well.
    """

    wells: Dict[str, Pool] = Field(default_factory=dict)
    well_capacity: Optional[float] = None

    def update_plate(self, new_contents: Dict[str, float]):
        """Updates the whole plate content"""
        for well_id, quantity in new_contents.items():
            if well_id in self.wells:
                self.wells[well_id].quantity = quantity
            else:
                self.wells[well_id] = Pool(
                    description=f"Well {well_id}",
                    name=f"Well{well_id}",
                    capacity=self.well_capacity,
                    quantity=quantity,
                )
