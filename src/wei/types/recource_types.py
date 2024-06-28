"""Recource Data Classes"""

from pydantic import BaseModel


class ResourceContainer(BaseModel):
    """"""

    information: str
    name: str
    capacity: float
    quantity: float = 0.0


class Pool(ResourceContainer):
    """"""

    pass


class StackQueue(ResourceContainer):
    """"""

    pass


class Collection(ResourceContainer):
    """"""

    pass
