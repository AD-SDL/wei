"""Resource Data Classes"""

from typing import Any, Dict, List, Optional, Union

import ulid
from pydantic import BaseModel, Field, computed_field


class Asset(BaseModel, extra="allow"):
    """
    Represents an asset (microplate) used for bio/chemistry experiments.

    Attributes:
        id (str): Unique identifier for the asset.
        name (str): Name of the asset.
    """

    id: str = Field(default_factory=lambda: str(ulid.new()))
    name: str = ""


class ResourceContainer(Asset, extra="allow"):
    """
    Base class for all resource containers.

    Attributes:
        description (str): Information about the resource.
        name (str): Name of the resource.
        capacity (float): Capacity of the resource.
        quantity (float): Current quantity of the resource.
    """

    description: str = ""
    capacity: Optional[Union[float, int]] = None


class Pool(ResourceContainer):
    """
    Class representing a continuous pool resource containing a single element.

    Methods:
        increase(amount: float): Increases the quantity by a specified amount.
        decrease(amount: float): Decreases the quantity by a specified amount.
        empty(): Empties the pool.
        fill(): Fills the pool to its capacity.
    """

    quantity: float = 0.0

    def increase(self, amount: float) -> None:
        """
        Increases the quantity by a specified amount.

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
        Decreases the quantity by a specified amount.

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
        """
        Empty by setting the quantity to zero.
        """
        self.quantity = 0.0

    def fill(self) -> None:
        """
        Sets the quantity to its capacity.
        """
        if self.capacity:
            self.quantity = self.capacity
        else:
            raise ValueError("Cannot fill without a defined capacity.")


class StackResource(ResourceContainer):
    """
    Class representing a stack resource.

    Attributes:
        contents (List[Any]): List of items in the stack/queue.

    Methods:
        push(instance: Any): Adds an instance to the stack/queue.
        pop(): Removes and returns the last instance from the stack/queue.
        contents(): Returns the contents of the stack/queue.
    """

    contents: List[Asset] = Field(default_factory=list)

    @computed_field
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
            int: The position of the instance in the stack/queue.

        Raises:
            ValueError: If the stack is full.
        """
        if not self.capacity or len(self.contents) < int(self.capacity):
            self.contents.append(instance)
        else:
            raise ValueError(f"Resource {self.name} is full.")

    def pop(self) -> Any:
        """
        Removes and returns the last instance from the stack.

        Returns:
            Any: The last instance in the stack.

        Raises:
            ValueError: If the stack is empty.
        """
        if self.contents:
            return self.contents.pop()
        else:
            raise ValueError(f"Resource {self.name} is empty.")


class QueueResource(ResourceContainer):
    """
    Class representing a queue-style resource.

    Attributes:
        contents (List[Any]): List of items in the queue.

    Methods:
        push(instance: Any): Adds an instance to the queue.
        pop(): Removes and returns the first instance from the queue.
        contents(): Returns the contents of the queue.
    """

    contents: List[Asset] = Field(default_factory=list)

    @computed_field
    @property
    def quantity(self) -> int:
        """Returns the number of assets in the resource container"""
        return len(self.contents)

    @quantity.setter
    def quantity(self, value: int):
        """Fill empty stack space with anonymous assets"""
        while len(self.contents) < value:
            self.push(Asset())

    def push(self, instance: Any) -> int:
        """
        Adds an instance to the queue.

        Args:
            instance (Any): The instance to add.

        Returns:
            int: The position of the instance in the queue.

        Raises:
            ValueError: If the queue is full.
        """
        if not self.capacity or self.quantity < int(self.capacity):
            self.contents.append(instance)
        else:
            raise ValueError(f"Resource {self.name} is full.")

    def pop(self) -> Any:
        """
        Removes and returns the last instance from the queue.

        Returns:
            Any: The last instance in the stack/queue.

        Raises:
            ValueError: If the stack/queue is empty.
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

    Methods:
        insert(location: str, instance: Any): Inserts an instance at a specific location.
        retrieve(location: str): Removes and returns the instance from a specific location.
    """

    contents: Dict[str, Any] = Field(default_factory=dict)

    @computed_field
    @property
    def quantity(self) -> int:
        """Returns the number of elements in the collection"""
        return len(self.contents.items())

    @quantity.setter
    def quantity(self, value: int):
        """Fill empty stack space with anonymous assets"""
        raise ValueError(
            "Collections do not support arbitrarily setting quantity. Please use the `insert` and `remove` methods instead."
        )

    def insert(self, location: str, instance: Any) -> None:
        """
        Inserts an instance at a specific location.

        Args:
            location (str): The location to insert the instance.
            instance (Any): The instance to insert.

        Raises:
            ValueError: If the collection is full.
        """
        if self.quantity < int(self.capacity):
            self.contents[location] = instance
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
            return self.contents.pop(location)
        else:
            raise ValueError("Invalid location.")


class Plate(Collection, extra="allow"):
    """
    Class representing a multi-welled plate.

    Attributes:
        id (str): Unique identifier for the plate.
        name (str): Name of the plate.
        wells (List[Pool]): List of pools representing wells in the plate.
    """

    contents: Dict[str, Pool] = Field(default_factory=dict)
    well_capacity: Optional[float] = None

    @computed_field
    @property
    def wells(self) -> Dict[str, Pool]:
        """Returns the contents of the plate"""
        return self.contents

    @wells.setter
    def wells(self, value: Pool):
        self.contents = value

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
