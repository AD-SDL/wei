"""Provides methods and classes to work with locations"""

from typing import Any, Union

from wei.core.data_classes import Location, Module, WorkflowRun
from wei.core.state_manager import StateManager

state_manager = StateManager()


def initialize_workcell_locations() -> None:
    """Initialize all locations in the workcell."""
    workcell = state_manager.get_workcell()
    for module_name in workcell.locations:
        for location_name, coordinates in workcell.locations[module_name].items():
            try:

                def update_coordinates(
                    location: Location, coordinates: Any, module_name: str
                ) -> Location:
                    location.coordinates[module_name] = coordinates
                    return location

                state_manager.update_location(
                    location_name, update_coordinates, coordinates, module_name
                )
            except KeyError:
                state_manager.set_location(
                    location_name,
                    Location(
                        name=location_name,
                        coordinates={module_name: coordinates},
                        state="Empty",
                        queue=[],
                    ),
                )


def update_location_reserve(module: Module, run_id: Union[str, None]) -> Module:
    """Updates a module's reservation"""
    module.reserved = run_id
    return module


def reserve_location(location: Location, run_id: str) -> None:
    """Reserve a location for a given run_id."""
    state_manager.update_location(location, update_location_reserve, run_id)


def clear_location_reservation(location: Location) -> None:
    """Reserve a location for a given run_id."""
    state_manager.update_location(location, update_location_reserve, None)


def reserve_source_and_target(wf_run: WorkflowRun) -> None:
    """Reserve the source and target location for a step."""
    step_index = wf_run.step_index
    step = wf_run.steps[step_index]

    if "source" in step.locations:
        reserve_location(step.locations["source"], wf_run.run_id)
    if "target" in step.locations:
        reserve_location(step.locations["target"], wf_run.run_id)


def free_source_and_target(wf_run: WorkflowRun) -> None:
    """Unreserve the source and target location for a step."""
    step_index = wf_run.step_index
    step = wf_run.steps[step_index]

    if "source" in step.locations:
        clear_location_reservation(step.locations["source"])
    if "target" in step.locations:
        clear_location_reservation(step.locations["target"])


def update_source_and_target(wf_run: WorkflowRun) -> None:
    """Update the source and target location and module after a step."""
    step_index = wf_run.step_index
    step = wf_run.steps[step_index]

    def update_location_state(
        object: Union[Location, Module], element: str
    ) -> Union[Location, Module]:
        object.state = element
        return object

    if "source" in step.locations:
        state_manager.update_location(
            step.locations["source"],
            update_location_state,
            "Empty",
        )
    if "target" in step.locations:
        if "trash" not in step.locations["target"]:
            state_manager.update_location(
                step.locations["target"],
                update_location_state,
                wf_run.experiment_id,
            )
