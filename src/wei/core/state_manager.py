"""
StateManager for WEI
"""

import warnings
from typing import Any, Callable, Dict, Union

import redis
from pottery import InefficientAccessWarning, RedisDict, Redlock
from pydantic import ValidationError

from wei.config import Config
from wei.types import Module, Workcell, WorkflowRun
from wei.types.base_types import ulid_factory
from wei.types.datapoint_types import DataPoint
from wei.types.event_types import Event
from wei.types.experiment_types import Campaign, Experiment
from wei.types.module_types import ModuleDefinition, ModuleStatus
from wei.types.workcell_types import Location


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
    def _lab_prefix(self) -> str:
        return f"{Config.lab_name}"

    @property
    def _workcell_prefix(self) -> str:
        return f"{self._lab_prefix}:{Config.workcell_name}"

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
                password=Config.redis_password if Config.redis_password else None,
            )
        return self._redis_connection

    @property
    def _locations(self) -> RedisDict:
        return RedisDict(
            key=f"{self._workcell_prefix}:locations", redis=self._redis_client
        )

    @property
    def _modules(self) -> RedisDict:
        return RedisDict(
            key=f"{self._workcell_prefix}:modules", redis=self._redis_client
        )

    @property
    def _workcell(self) -> RedisDict:
        return RedisDict(
            key=f"{self._workcell_prefix}:workcell", redis=self._redis_client
        )

    @property
    def _workflow_runs(self) -> RedisDict:
        return RedisDict(
            key=f"{self._workcell_prefix}:workflow_runs", redis=self._redis_client
        )

    @property
    def _experiments(self) -> RedisDict:
        return RedisDict(
            key=f"{self._lab_prefix}:experiments", redis=self._redis_client
        )

    @property
    def _campaigns(self) -> RedisDict:
        return RedisDict(key=f"{self._lab_prefix}:campaigns", redis=self._redis_client)

    @property
    def _events(self) -> RedisDict:
        return RedisDict(key=f"{self._lab_prefix}:events", redis=self._redis_client)

    @property
    def _datapoints(self) -> RedisDict:
        return RedisDict(key=f"{self._lab_prefix}:datapoints", redis=self._redis_client)

    @property
    def paused(self) -> bool:
        """Get the pause state of the workcell"""
        return self._redis_client.get(f"{self._workcell_prefix}:paused") == "true"

    @paused.setter
    def paused(self, value: bool) -> None:
        """Set the pause state of the workcell"""
        self._redis_client.set(
            f"{self._workcell_prefix}:paused", "true" if value else "false"
        )

    @property
    def locked(self) -> bool:
        """Get the lock state of the workcell"""
        return self._redis_client.get(f"{self._workcell_prefix}:locked") == "true"

    @locked.setter
    def locked(self, value: bool) -> None:
        """Set the lock state of the workcell"""
        self._redis_client.set(
            f"{self._workcell_prefix}:locked", "true" if value else "false"
        )

    @property
    def shutdown(self) -> bool:
        """Get the shutdown state of the workcell"""
        return self._redis_client.get(f"{self._workcell_prefix}:shutdown") == "true"

    @shutdown.setter
    def shutdown(self, value: bool) -> None:
        """Set the shutdown state of the workcell"""
        self._redis_client.set(
            f"{self._workcell_prefix}:shutdown", "true" if value else "false"
        )

    # *Locking Methods
    def campaign_lock(self, campaign_id: str) -> Redlock:
        """
        Get a lock on a particular campaign. This should be called before editing a Campaign.
        """
        return Redlock(
            key="f{self._lab_prefix}:campaign_lock:{campaign_id}",
            masters={self._redis_client},
            auto_release_time=60,
        )

    def experiment_lock(self, experiment_id: str) -> Redlock:
        """
        Get a lock on a particular experiment. This should be called before editing an experiment.
        """
        return Redlock(
            key="f{self._lab_prefix}:experiment_lock:{experiment_id}",
            masters={self._redis_client},
            auto_release_time=60,
        )

    def wc_state_lock(self) -> Redlock:
        """
        Gets a lock on the workcell's state. This should be called before any state updates are made,
        or where we don't want the state to be changing underneath us (i.e., in the engine).
        """
        return Redlock(
            key=f"{self._workcell_prefix}:state_lock",
            masters={self._redis_client},
            auto_release_time=60,
        )

    # *State Methods
    def get_state(self) -> Dict[str, Dict[Any, Any]]:
        """
        Return a dict containing the current state of the workcell.
        """
        return {
            "status": self.wc_status,
            "error": self.error,
            "locations": self._locations.to_dict(),
            "modules": self._modules.to_dict(),
            # "config": Config.dump_to_json(),
            "workflows": self._workflow_runs.to_dict(),
            "workcell": self._workcell.to_dict(),
            "paused": self.paused,
            "locked": self.locked,
            "shutdown": self.shutdown,
        }

    @property
    def wc_status(self) -> ModuleStatus:
        """The current status of the workcell"""
        return self._redis_client.get(f"{self._workcell_prefix}:status")

    @wc_status.setter
    def wc_status(self, value: ModuleStatus) -> None:
        """Set the status of the workcell"""
        if self.wc_status != value:
            self.mark_state_changed()
        self._redis_client.set(f"{self._workcell_prefix}:status", value)

    @property
    def error(self) -> str:
        """Latest error on the server"""
        return self._redis_client.get(f"{self._workcell_prefix}:error")

    @error.setter
    def error(self, value: str) -> None:
        """Add an error to the workcell's error deque"""
        if self.error != value:
            self.mark_state_changed()
        return self._redis_client.set(f"{self._workcell_prefix}:error", value)

    def clear_state(
        self, reset_locations: bool = True, clear_workflow_runs: bool = False
    ) -> None:
        """
        Clears the state of the workcell, optionally leaving the locations state intact.
        """
        self._modules.clear()
        if reset_locations:
            self._locations.clear()
        if clear_workflow_runs:
            self._workflow_runs.clear()
        self._workcell.clear()
        self.state_change_marker = "0"
        self.paused = False
        self.locked = False
        self.shutdown = False
        self.mark_state_changed()

    def mark_state_changed(self) -> int:
        """Marks the state as changed and returns the current state change counter"""
        return int(self._redis_client.incr(f"{self._workcell_prefix}:state_changed"))

    def has_state_changed(self) -> bool:
        """Returns True if the state has changed since the last time this method was called"""
        state_change_marker = self._redis_client.get(
            f"{self._workcell_prefix}:state_changed"
        )
        if state_change_marker != self.state_change_marker:
            self.state_change_marker = state_change_marker
            return True
        else:
            return False

    # *Campaign Methods
    def get_campaign(self, campaign_id: str) -> Campaign:
        """
        Returns a campaign by ID
        """
        return Campaign.model_validate(self._campaigns[campaign_id])

    def get_all_campaigns(self) -> Dict[str, Campaign]:
        """
        Returns all campaigns
        """
        valid_campaigns = {}
        for campaign_id, campaign in self._campaigns.to_dict().items():
            try:
                valid_campaigns[str(campaign_id)] = Campaign.model_validate(campaign)
            except ValidationError:
                continue
        return valid_campaigns

    def set_campaign(self, campaign: Campaign) -> None:
        """
        Sets a campaign by ID
        """
        self._campaigns[campaign.campaign_id] = campaign.model_dump(mode="json")

    def delete_campaign(self, campaign_id: str) -> None:
        """
        Deletes a campaign by ID
        """
        del self._campaigns[campaign_id]

    def update_campaign(
        self, campaign_id: str, func: Callable[..., Any], *args: Any, **kwargs: Any
    ) -> None:
        """
        Updates the state of a campaign.
        """
        self.set_campaign(func(self.get_campaign(campaign_id), *args, **kwargs))

    # *Experiment Methods
    def get_experiment(self, experiment_id: str) -> Experiment:
        """
        Returns an experiment by ID
        """
        return Experiment.model_validate(self._experiments[experiment_id])

    def get_all_experiments(self) -> Dict[str, Experiment]:
        """
        Returns all experiments
        """
        valid_experiments = {}
        for experiment_id, experiment in self._experiments.to_dict().items():
            try:
                valid_experiments[str(experiment_id)] = Experiment.model_validate(
                    experiment, from_attributes=True
                )
            except ValidationError:
                continue
        return valid_experiments

    def set_experiment(self, experiment: Experiment) -> None:
        """
        Sets an experiment by ID
        """
        self._experiments[experiment.experiment_id] = experiment.model_dump(mode="json")

    def delete_experiment(self, experiment_id: str) -> None:
        """
        Deletes an experiment by ID
        """
        del self._experiments[experiment_id]

    def update_experiment(
        self, experiment_id: str, func: Callable[..., Any], *args: Any, **kwargs: Any
    ) -> None:
        """
        Updates the state of an experiment.
        """
        self.set_experiment(func(self.get_experiment(experiment_id), *args, **kwargs))

    # *Event Methods
    def get_event(self, event_id: str) -> Event:
        """
        Returns an event by ID
        """
        return Event.model_validate(self._events[event_id])

    def get_all_events(self) -> Dict[str, Event]:
        """
        Returns all events
        """
        from pydantic import ValidationError

        valid_events = {}
        for event_id, event in self._events.to_dict().items():
            try:
                valid_events[str(event_id)] = Event.model_validate(event)
            except ValidationError:
                continue
        return valid_events

    def set_event(self, event: Event) -> None:
        """
        Sets an event by ID
        """
        self._events[event.event_id] = event.model_dump(mode="json")

    # *DataPoint Methods
    def get_datapoint(self, data_id: str) -> DataPoint:
        """
        Returns an event by ID
        """
        return DataPoint.model_validate(
            self._datapoints[data_id], from_attributes=True, strict=False
        )

    def get_all_datapoints(self) -> Dict[str, DataPoint]:
        """
        Returns all datapoints
        """
        valid_datapoints = {}
        for datapoint_id, datapoint in self._datapoints.to_dict().items():
            try:
                valid_datapoints[str(datapoint_id)] = DataPoint.model_validate(
                    datapoint
                )
            except ValidationError:
                continue
        return valid_datapoints

    def set_datapoint(self, datapoint: DataPoint) -> None:
        """
        Sets an event by ID
        """
        self._datapoints[datapoint.id] = datapoint.model_dump(mode="json")

    # *Workcell Methods
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

    def get_workcell_id(self) -> str:
        """
        Returns the workcell ID
        """
        wc_id = self._redis_client.get(f"{self._workcell_prefix}:workcell_id")
        if wc_id is None:
            self._redis_client.set(
                f"{self._workcell_prefix}:workcell_id", ulid_factory()
            )
            wc_id = self._redis_client.get(f"{self._workcell_prefix}:workcell_id")
        return wc_id

    # *Workflow Methods
    def get_workflow_run(self, run_id: Union[str, str]) -> WorkflowRun:
        """
        Returns a workflow by ID
        """
        return WorkflowRun.model_validate(self._workflow_runs[str(run_id)])

    def get_all_workflow_runs(self) -> Dict[str, WorkflowRun]:
        """
        Returns all workflow runs
        """
        valid_workflow_runs = {}
        for run_id, workflow_run in self._workflow_runs.to_dict().items():
            try:
                valid_workflow_runs[str(run_id)] = WorkflowRun.model_validate(
                    workflow_run
                )
            except ValidationError:
                continue
        return valid_workflow_runs

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

    # *Location Methods
    def get_location(self, location_name: str) -> Location:
        """
        Returns a location by name
        """
        return Location.model_validate(self._locations[location_name])

    def get_all_locations(self) -> Dict[str, Location]:
        """
        Returns all locations
        """
        valid_locations = {}
        for location_name, location in self._locations.to_dict().items():
            try:
                valid_locations[str(location_name)] = Location.model_validate(location)
            except ValidationError:
                continue
        return valid_locations

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

    # *Module Methods
    def get_module(self, module_name: str) -> Module:
        """
        Returns a module by name
        """
        return Module.model_validate(self._modules[module_name])

    def get_all_modules(self) -> Dict[str, Module]:
        """
        Returns all modules
        """
        valid_modules = {}
        for module_name, module in self._modules.to_dict().items():
            try:
                valid_modules[str(module_name)] = Module.model_validate(module)
            except ValidationError:
                continue
        return valid_modules

    def set_module(
        self, module_name: str, module: Union[Module, ModuleDefinition, Dict[str, Any]]
    ) -> None:
        """
        Sets a module by name
        """
        if isinstance(module, Module):
            module_dump = module.model_dump(mode="json")
        elif isinstance(module, ModuleDefinition):
            module_dump = Module.model_validate(
                module, from_attributes=True
            ).model_dump(mode="json")
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


state_manager = StateManager()
