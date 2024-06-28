"""Recource Data Classes"""

from pydantic import BaseModel


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


class Pool(ResourceContainer):
    """
    Class representing a continuous pool resource.

    Methods:
        increase(amount: float): Increases the quantity by a specified amount.
        decrease(amount: float): Decreases the quantity by a specified amount.
        empty(): Empties the pool.
        fill(): Fills the pool to its capacity.
    """

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

    pass


class Collection(ResourceContainer):
    """
    Class representing a collection resource.

    Attributes:
        contents (Dict[str, Any]): Dictionary of items in the collection.

    Methods:
        insert(location: str, instance: Any): Inserts an instance at a specific location.
        retrieve(location: str): Removes and returns the instance from a specific location.
    """

    pass
