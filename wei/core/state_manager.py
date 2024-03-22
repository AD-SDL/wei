"""
StateManager for WEI
"""

import warnings
from typing import Any, Callable, Dict, Union

import redis
from pottery import InefficientAccessWarning, RedisDict, Redlock

from wei.config import Config
from wei.core.data_classes import Location, Module, Workcell, WorkflowRun


class StateManager:
    """
    Manages state for WEI, providing transactional access to reading and writing state with
    optimistic check-and-set and locking.
    """

    state_change_marker = "0"
    _redis_connection: Any = None

    def __init__(self) -> None:
        """
        Initialize a StateManager for a given workcell.
        """
        warnings.filterwarnings("ignore", category=InefficientAccessWarning)

    @property
    def _prefix(self) -> str:
        return f"wei:{Config.workcell_name}"

    @property
    def _redis_client(self) -> Any:
        """
        Returns a redis.Redis client, but only creates one connection.
        MyPy can't handle Redis object return types for some reason, so no type-hinting.
        """
        if self._redis_connection is None:
            self._redis_connection = redis.Redis(
                host=str(Config.redis_host),
                port=int(Config.redis_port),
                db=0,
                decode_responses=True,
            )
        return self._redis_connection

    @property
    def _locations(self) -> RedisDict:
        return RedisDict(key=f"{self._prefix}:locations", redis=self._redis_client)

    @property
    def _modules(self) -> RedisDict:
        return RedisDict(key=f"{self._prefix}:modules", redis=self._redis_client)

    @property
    def _workcell(self) -> RedisDict:
        return RedisDict(key=f"{self._prefix}:workcell", redis=self._redis_client)

    @property
    def _workflow_runs(self) -> RedisDict:
        return RedisDict(key=f"{self._prefix}:workflow_runs", redis=self._redis_client)

    # Locking Methods
    def state_lock(self) -> Redlock:
        """
        Gets a lock on the state. This should be called before any state updates are made,
        or where we don't want the state to be changing underneath us (i.e., in the engine).
        """
        return Redlock(
            key=f"{self._prefix}:state",
            masters={self._redis_client},
            auto_release_time=60,
        )

    # State Methods
    def get_state(self) -> Dict[str, Dict[Any, Any]]:
        """
        Return a dict containing the current state of the workcell.
        """
        return {
            "locations": self._locations.to_dict(),
            "modules": self._modules.to_dict(),
            "workflows": self._workflow_runs.to_dict(),
            "workcell": self._workcell.to_dict(),
        }

    def clear_state(self, reset_locations: bool = True) -> None:
        """
        Clears the state of the workcell, optionally leaving the locations state intact.
        """
        self._modules.clear()
        if reset_locations:
            self._locations.clear()
        self._workflow_runs.clear()
        self._workcell.clear()
        self.state_change_marker = "0"
        # self._redis_client.set(f"{self._prefix}:state_changed", "0")
        self.mark_state_changed()

    def mark_state_changed(self) -> int:
        """Marks the state as changed and returns the current state change counter"""
        return int(self._redis_client.incr(f"{self._prefix}:state_changed"))

    def has_state_changed(self) -> bool:
        """Returns True if the state has changed since the last time this method was called"""
        state_change_marker = self._redis_client.get(f"{self._prefix}:state_changed")
        if state_change_marker != self.state_change_marker:
            self.state_change_marker = state_change_marker
            return True
        else:
            return False

    # Workcell Methods
    def get_workcell(self) -> Workcell:
        """
        Returns the current workcell as a Workcell object
        """
        return Workcell.model_validate(self._workcell.to_dict())

    def set_workcell(self, workcell: Workcell) -> None:
        """
        Sets the active workcell
        """
        self._workcell.update(**workcell.model_dump(mode="json"))

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

    def get_all_workflow_runs(self) -> Dict[str, WorkflowRun]:
        """
        Returns all workflows
        """
        return {
            str(run_id): WorkflowRun.model_validate(workflow_run)
            for run_id, workflow_run in self._workflow_runs.to_dict().items()
        }

    def set_workflow_run(self, wf: WorkflowRun) -> None:
        """
        Sets a workflow by ID
        """
        if isinstance(wf, WorkflowRun):
            wf_dump = wf.model_dump(mode="json")
        else:
            wf_dump = WorkflowRun.model_validate(wf).model_dump(mode="json")
        self._workflow_runs[str(wf_dump["run_id"])] = wf_dump
        self.mark_state_changed()

    def delete_workflow_run(self, run_id: Union[str, str]) -> None:
        """
        Deletes a workflow by ID
        """
        del self._workflow_runs[str(run_id)]
        self.mark_state_changed()

    def update_workflow_run(
        self, run_id: str, func: Callable[..., Any], *args: Any, **kwargs: Any
    ) -> None:
        """
        Updates the state of a workflow.
        """
        self.set_workflow_run(func(self.get_workflow_run(run_id), *args, **kwargs))

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
            str(location_name): Location.model_validate(location)
            for location_name, location in self._locations.to_dict().items()
        }

    def set_location(
        self, location_name: str, location: Union[Location, Dict[str, Any]]
    ) -> None:
        """
        Sets a location by name
        """
        if isinstance(location, Location):
            location_dump = location.model_dump(mode="json")
        else:
            location_dump = Location.model_validate(location).model_dump(mode="json")
        self._locations[location_name] = location_dump
        self.mark_state_changed()

    def delete_location(self, location_name: str) -> None:
        """
        Deletes a location by name
        """
        del self._locations[location_name]
        self.mark_state_changed()

    def update_location(
        self, location_name: str, func: Callable[..., Any], *args: Any, **kwargs: Any
    ) -> None:
        """
        Updates the state of a location.
        """
        self.set_location(
            location_name, func(self.get_location(location_name), *args, **kwargs)
        )

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
            str(module_name): Module.model_validate(module)
            for module_name, module in self._modules.to_dict().items()
        }

    def set_module(
        self, module_name: str, module: Union[Module, Dict[str, Any]]
    ) -> None:
        """
        Sets a module by name
        """
        if isinstance(module, Module):
            module_dump = module.model_dump(mode="json")
        else:
            module_dump = Module.model_validate(module).model_dump(mode="json")
        self._modules[module_name] = module_dump
        self.mark_state_changed()

    def delete_module(self, module_name: str) -> None:
        """
        Deletes a module by name
        """
        del self._modules[module_name]
        self.mark_state_changed()

    def update_module(
        self, module_name: str, func: Callable[..., Any], *args: Any, **kwargs: Any
    ) -> None:
        """
        Updates the state of a module.
        """
        self.set_module(
            module_name, func(self.get_module(module_name), *args, **kwargs)
        )
