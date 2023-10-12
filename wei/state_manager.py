"""
StateManager for WEI
"""


import json
from typing import Any, Callable, Union
from uuid import UUID

import redis
from pottery import RedisDict, Redlock

from wei.core.data_classes import Module, WorkcellData, Workflow, WorkflowRun


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
        self._locations = RedisDict(
            key=f"{self._prefix}:locations", redis=self._redis_server
        )
        self._modules = RedisDict(
            key=f"{self._prefix}:modules", redis=self._redis_server
        )
        self._workflow_runs = RedisDict(
            key=f"{self._prefix}:workflows", redis=self._redis_server
        )
        self._workcell = RedisDict(
            key=f"{self._prefix}:workcell", redis=self._redis_server
        )

    # Locking Methods
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

    # State Methods
    def get_state(self) -> dict:
        """
        Return a dict containing the current state of the workcell.
        """
        return {
            "locations": self._locations.to_dict(),
            "modules": self._modules.to_dict(),
            "workflows": self._workflow_runs.to_dict(),
            "workcell": self._workcell.to_dict(),
        }

    def clear_state(self, reset_locations=True) -> None:
        """
        Clears the state of the workcell, optionally leaving the locations state intact.
        """
        self._modules.clear()
        if reset_locations:
            self._locations.clear()
        self._workflow_runs.clear()
        self._workcell.clear()

    # Workcell Methods
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

    # Workflow Methods
    def get_workflow_run(self, run_id: Union[str, UUID]) -> Workflow:
        """
        Returns a workflow by ID
        """
        return WorkflowRun(**self._workflow_runs[run_id])

    def set_workflow_run(self, wf: WorkflowRun) -> None:
        """
        Sets a workflow by ID
        """
        self._workflow_runs[wf.run_id] = json.loads(wf.json())

    def delete_workflow_run(self, run_id: Union[str, UUID]) -> None:
        """
        Deletes a workflow by ID
        """
        del self._workflow_runs[run_id]

    def update_workflow_run(self, run_id: str, func: Callable, *args) -> None:
        """
        Updates the state of a workflow.
        """
        wf = self._workflow_runs[run_id]
        self._workflow_runs[run_id] = func(wf, *args)


    # Location Methods
    def get_location(self, location_name: str) -> dict:
        """
        Returns a location by name
        """
        return self._locations[location_name]

    def set_location(self, location_name: str, location: Any) -> None:
        """
        Sets a location by name
        """
        self._locations[location_name] = location

    def delete_location(self, location_name: str) -> None:
        """
        Deletes a location by name
        """
        del self._locations[location_name]

    def update_location(self, location_name: str, func: Callable, *args) -> None:
        """
        Updates the state of a location.
        """
        location = self._locations[location_name]
        self._locations[location_name] = func(location, *args)

    # Module Methods
    def get_module(self, module_name: str) -> dict:
        """
        Returns a module by name
        """
        return Module(**self._modules[module_name])

    def set_module(self, module_name: str, module: Module) -> None:
        """
        Sets a module by name
        """
        self._modules[module_name] = json.loads(module.json())

    def delete_module(self, module_name: str) -> None:
        """
        Deletes a module by name
        """
        del self._modules[module_name]

    def update_module(self, module_name: str, func: Callable, *args) -> None:
        """
        Updates the state of a module.
        """
        module = self._modules[module_name]
        self._modules[module_name] = func(module, *args)
