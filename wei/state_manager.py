"""
StateManager for WEI
"""


import json
from typing import Callable

import redis
from pottery import RedisDict, Redlock

from wei.core.data_classes import WorkcellData


class StateManager:
    """
    Manages state for WEI, providing transactional access to reading and writing state with
    optimistic check-and-set and locking.
    """

    def __init__(
        self, workcell_name: str, redis_host="127.0.0.1", redis_port=6379
    ) -> None:
        """
        Initialize a StateManager for a given workcell.
        """
        self._prefix = f"wei:{workcell_name}"
        self._redis_server = redis.Redis(
            host=redis_host, port=redis_port, decode_responses=True
        )
        self.locations = RedisDict(
            key=f"{self._prefix}:locations", redis=self._redis_server
        )
        self.modules = RedisDict(
            key=f"{self._prefix}:modules", redis=self._redis_server
        )
        self.workflows = RedisDict(
            key=f"{self._prefix}:workflows", redis=self._redis_server
        )
        self._workcell = RedisDict(
            key=f"{self._prefix}:workcell", redis=self._redis_server
        )

    def get_workcell(self) -> WorkcellData:
        """
        Returns the current workcell as a WorkcellData object
        """
        return WorkcellData(**self._workcell.to_dict())

    def set_workcell(self, workcell: WorkcellData) -> None:
        """
        Sets the active workcell
        """
        self._workcell.update(json.loads(workcell.json()))

    def clear_workcell(self) -> None:
        """
        Empty the workcell definition
        """
        self._workcell.clear()

    def get_state(self) -> dict:
        """
        Return a dict containing the current state of the workcell.
        """
        return {
            "locations": self.locations.to_dict(),
            "modules": self.modules.to_dict(),
            "workflows": self.workflows.to_dict(),
        }

    def state_lock(self) -> Redlock:
        """
        Gets a lock on the state. This should be called before any state updates are made,
        or where we don't want the state to be changing underneath us (i.e., in the scheduler).
        """
        return Redlock(key=f"{self._prefix}:state", masters={self._redis_server})

    def is_state_locked(self) -> bool:
        """
        Returns true if the state is locked
        """
        return bool(self.state_lock().locked())

    def clear_state(self, reset_locations=True) -> None:
        """
        Clears the state of the workcell, optionally leaving the locations state intact.
        """
        self.modules.clear()
        if reset_locations:
            self.locations.clear()
        self.workflows.clear()
        self._workcell.clear()

    def update_workflow(self, wf_id: str, func: Callable, *args) -> None:
        """
        Updates the state of a workflow.
        """
        wf = self.workflows[wf_id]
        self.workflows[wf_id] = func(wf, *args)

    def update_location(self, location_name: str, func: Callable, *args) -> None:
        """
        Updates the state of a location.
        """
        location = self.locations[location_name]
        self.locations[location_name] = func(location, *args)

    def update_module(self, module_name: str, func: Callable, *args) -> None:
        """
        Updates the state of a module.
        """
        module = self.modules[module_name]
        self.modules[module_name] = func(module, *args)
