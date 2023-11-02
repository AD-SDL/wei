"""
StateManager for WEI
"""


import warnings
from typing import Callable, Dict, Union

import redis
from pottery import InefficientAccessWarning, RedisDict, Redlock

from wei.core.data_classes import Location, Module, WorkcellData, WorkflowRun


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
        warnings.filterwarnings("ignore", category=InefficientAccessWarning)
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
        or where we don't want the state to be changing underneath us (i.e., in the engine).
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
        return WorkcellData.model_validate(self._workcell.to_dict())

    def set_workcell(self, workcell: WorkcellData) -> None:
        """
        Sets the active workcell
        """
        self._workcell.update(workcell.model_dump(mode="json"))

    def clear_workcell(self) -> None:
        """
        Empty the workcell definition
        """
        self._workcell.clear()

    # Workflow Methods
    def get_workflow_run(self, run_id: Union[str, str]) -> WorkflowRun:
        """
        Returns a workflow by ID
        """
        return WorkflowRun.model_validate(self._workflow_runs[str(run_id)])

    def get_all_workflow_runs(self) -> Dict[Union[str, str], WorkflowRun]:
        """
        Returns all workflows
        """
        return {
            run_id: WorkflowRun.model_validate(workflow_run)
            for run_id, workflow_run in self._workflow_runs.to_dict().items()
        }

    def set_workflow_run(self, run_id: Union[str, str], wf: WorkflowRun) -> None:
        """
        Sets a workflow by ID
        """
        if isinstance(wf, WorkflowRun):
            wf = wf.model_dump()
        else:
            wf = WorkflowRun.model_validate(wf).model_dump(mode="json")
        self._workflow_runs[str(run_id)] = wf

    def delete_workflow_run(self, run_id: Union[str, str]) -> None:
        """
        Deletes a workflow by ID
        """
        del self._workflow_runs[str(run_id)]

    def update_workflow_run(self, run_id: str, func: Callable, *args) -> None:
        """
        Updates the state of a workflow.
        """
        self.set_workflow_run(str(run_id), func(self.get_workflow_run(run_id), *args))

    # Location Methods
    def get_location(self, location_name: str) -> Location:
        """
        Returns a location by name
        """
        return Location.model_validate(self._locations[location_name])

    def get_all_locations(self) -> Dict[str, Location]:
        """
        Returns all locations
        """
        return {
            location_name: Location.model_validate(location)
            for location_name, location in self._locations.to_dict().items()
        }

    def set_location(self, location_name: str, location: Union[Location, Dict]) -> None:
        """
        Sets a location by name
        """
        if isinstance(location, Location):
            location = location.model_dump(mode="json")
        else:
            location = Location.model_validate(location).model_dump(mode="json")
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
        self.set_location(location_name, func(self.get_location(location_name), *args))

    # Module Methods
    def get_module(self, module_name: str) -> Module:
        """
        Returns a module by name
        """
        return Module.model_validate(self._modules[module_name])

    def get_all_modules(self) -> Dict[str, Module]:
        """
        Returns a module by name
        """
        return {
            module_name: Module.model_validate(module)
            for module_name, module in self._modules.to_dict().items()
        }

    def set_module(self, module_name: str, module: Union[Module, Dict]) -> None:
        """
        Sets a module by name
        """
        if isinstance(module, Module):
            module = module.model_dump(mode="json")
        else:
            module = Module.model_validate(module).model_dump(mode="json")
        self._modules[module_name] = module

    def delete_module(self, module_name: str) -> None:
        """
        Deletes a module by name
        """
        del self._modules[module_name]

    def update_module(self, module_name: str, func: Callable, *args) -> None:
        """
        Updates the state of a module.
        """
        self.set_module(module_name, func(self.get_module(module_name), *args))
