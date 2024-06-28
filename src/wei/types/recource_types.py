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
