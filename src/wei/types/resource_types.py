"""Resource Data Classes"""

import json
from typing import Any, Dict, List, Optional

import ulid
from sqlalchemy import Column, Text
from sqlmodel import Field as SQLField
from sqlmodel import SQLModel


class Asset(SQLModel, table=True):
    """
    Represents an asset (microplate) used for bio/chemistry experiments.

    Attributes:
        id (str): Unique identifier for the asset.
        name (str): Name of the asset.
    """

    id: str = SQLField(default_factory=lambda: str(ulid.new()), primary_key=True)
    name: str = SQLField(default="")


class ResourceContainer(Asset, table=True):
    """
    Base class for all resource containers.

    Attributes:
        description (str): Information about the resource.
        capacity (Optional[Union[float, int]]): Capacity of the resource.
    """

    description: str = SQLField(default="")
    capacity: Optional[float] = SQLField(default=None, nullable=True)


class Pool(ResourceContainer, table=True):
    """
    Class representing a continuous pool resource containing a single element.

    Methods:
        increase(amount: float): Increases the quantity by a specified amount.
        decrease(amount: float): Decreases the quantity by a specified amount.
        empty(): Empties the pool.
        fill(): Fills the pool to its capacity.
    """

    quantity: float = SQLField(default=0.0)

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


class StackResource(ResourceContainer, table=True):
    """
    Class representing a stack resource.

    Attributes:
        contents (List[Any]): List of items in the stack/queue.

    Methods:
        push(instance: Any): Adds an instance to the stack/queue.
        pop(): Removes and returns the last instance from the stack/queue.
        contents(): Returns the contents of the stack/queue.
    """

    contents: str = SQLField(sa_column=Column(Text, default="[]"))

    @property
    def contents_list(self) -> List[Asset]:
        """Returns the contents as a list of assets"""
        return [Asset.from_json(item) for item in json.loads(self.contents)]

    @property
    def quantity(self) -> int:
        """Returns the number of assets in the stack resource container"""
        return len(self.contents_list)

    @quantity.setter
    def quantity(self, value: int):
        """Fill empty stack space with anonymous assets"""
        contents = self.contents_list
        while len(contents) < value:
            contents.append(Asset())
        self.contents = json.dumps([item.model_dump_json() for item in contents])

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
        contents = self.contents_list
        if not self.capacity or len(contents) < int(self.capacity):
            contents.append(instance)
            self.contents = json.dumps([item.model_dump_json() for item in contents])
        else:
            raise ValueError(f"Resource {self.name} is full.")
        return len(contents) - 1

    def pop(self) -> Any:
        """
        Removes and returns the last instance from the stack.

        Returns:
            Any: The last instance in the stack.

        Raises:
            ValueError: If the stack is empty.
        """
        contents = self.contents_list
        if contents:
            instance = contents.pop()
            self.contents = json.dumps([item.model_dump_json() for item in contents])
            return instance
        else:
            raise ValueError(f"Resource {self.name} is empty.")


class QueueResource(ResourceContainer, table=True):
    """
    Class representing a queue-style resource.

    Attributes:
        contents (List[Any]): List of items in the queue.

    Methods:
        push(instance: Any): Adds an instance to the queue.
        pop(): Removes and returns the first instance from the queue.
        contents(): Returns the contents of the queue.
    """

    contents: str = SQLField(sa_column=Column(Text, default="[]"))

    @property
    def contents_list(self) -> List[Asset]:
        """Returns the contents as a list of assets"""
        return [Asset.from_json(item) for item in json.loads(self.contents)]

    @property
    def quantity(self) -> int:
        """Returns the number of assets in the resource container"""
        return len(self.contents_list)

    @quantity.setter
    def quantity(self, value: int):
        """Fill empty stack space with anonymous assets"""
        contents = self.contents_list
        while len(contents) < value:
            contents.append(Asset())
        self.contents = json.dumps([item.model_dump_json() for item in contents])

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
        contents = self.contents_list
        if not self.capacity or self.quantity < int(self.capacity):
            contents.append(instance)
            self.contents = json.dumps([item.model_dump_json() for item in contents])
        else:
            raise ValueError(f"Resource {self.name} is full.")
        return len(contents) - 1

    def pop(self) -> Any:
        """
        Removes and returns the first instance from the queue.

        Returns:
            Any: The first instance in the queue.

        Raises:
            ValueError: If the queue is empty.
        """
        contents = self.contents_list
        if contents:
            instance = contents.pop(0)
            self.contents = json.dumps([item.model_dump_json() for item in contents])
            return instance
        else:
            raise ValueError(f"Resource {self.name} is empty.")


class Collection(ResourceContainer, table=True):
    """
    Class representing a resource container that allows random access.

    Attributes:
        contents (Dict[str, Any]): Dictionary of items in the collection.

    Methods:
        insert(location: str, instance: Any): Inserts an instance at a specific location.
        retrieve(location: str): Removes and returns the instance from a specific location.
    """

    contents: str = SQLField(sa_column=Column(Text, default="{}"))

    @property
    def contents_dict(self) -> Dict[str, Asset]:
        """Returns the contents as a dictionary of assets"""
        return {k: Asset.from_json(v) for k, v in json.loads(self.contents).items()}

    @property
    def quantity(self) -> int:
        """Returns the number of elements in the collection"""
        return len(self.contents_dict)

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
        contents = self.contents_dict
        if self.quantity < int(self.capacity):
            contents[location] = instance
            self.contents = json.dumps(
                {k: v.model_dump_json() for k, v in contents.items()}
            )
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
        contents = self.contents_dict
        if location and location in contents:
            instance = contents.pop(location)
            self.contents = json.dumps(
                {k: v.model_dump_json() for k, v in contents.items()}
            )
            return instance
        else:
            raise ValueError("Invalid location.")


class Plate(Collection, table=True):
    """
    Class representing a multi-welled plate.

    Attributes:
        id (str): Unique identifier for the plate.
        name (str): Name of the plate.
        wells (List[Pool]): List of pools representing wells in the plate.
    """

    well_capacity: Optional[float] = None

    @property
    def wells(self) -> Dict[str, Pool]:
        """Returns the contents of the plate"""
        return {k: Pool.from_json(v) for k, v in self.contents_dict.items()}

    @wells.setter
    def wells(self, value: Dict[str, Pool]):
        self.contents = json.dumps({k: v.model_dump_json() for k, v in value.items()})

    def update_plate(self, new_contents: Dict[str, float]):
        """Updates the whole plate content"""
        wells = self.wells
        for well_id, quantity in new_contents.items():
            if well_id in wells:
                wells[well_id].quantity = quantity
            else:
                wells[well_id] = Pool(
                    description=f"Well {well_id}",
                    name=f"Well{well_id}",
                    capacity=self.well_capacity,
                    quantity=quantity,
                )
        self.wells = wells
