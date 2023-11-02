"""Provides methods and classes to work with locations"""

from wei.core.config import Config
from wei.core.data_classes import Location, WorkflowRun

state_manager = Config.state_manager


def initialize_workcell_locations():
    workcell = state_manager.get_workcell()
    for module_name in workcell.locations:
        for location_name, coordinates in workcell.locations[module_name].items():
            try:

                def update_coordinates(location, coordinates, module_name):
                    location.coordinates[module_name] = coordinates

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


def update_source_and_target(wf_run: WorkflowRun) -> None:
    """Update the source and target location and module of a workflow."""
    step_index = wf_run.step_index
    steps = wf_run.steps

    # Define some helper functions to update the "queue" properties of modules and locations
    def remove_element_from_queue(object, element):
        try:
            object.queue.remove(element)
        except ValueError:
            pass
        return object

    def append_element_to_queue(object, element):
        object.queue.append(element)
        return object

    def update_location_state(object, element):
        object.state = element
        return object

    if step_index < len(wf_run.steps):
        if "target" in steps[step_index].locations:
            state_manager.update_location(
                steps[step_index].locations["target"],
                append_element_to_queue,
                wf_run.run_id,
            )
        state_manager.update_module(
            steps[step_index].module, append_element_to_queue, wf_run.run_id
        )

    if step_index > 0:
        state_manager.update_module(
            steps[step_index - 1].module,
            remove_element_from_queue,
            wf_run.run_id,
        )
        if "source" in steps[step_index - 1].locations:
            state_manager.update_location(
                steps[step_index - 1].locations["source"],
                update_location_state,
                "Empty",
            )
        if "target" in steps[step_index - 1].locations:
            if not ("trash" in steps[step_index - 1].locations["target"]):
                state_manager.update_location(
                    steps[step_index - 1].locations["target"],
                    update_location_state,
                    wf_run.experiment_id,
                )
            state_manager.update_location(
                steps[step_index - 1].locations["target"],
                remove_element_from_queue,
                wf_run.run_id,
            )
