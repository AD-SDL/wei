"""
REST-based node that interfaces with WEI and provides various fake actions for testing purposes
"""

from typing import Annotated

from fastapi import UploadFile
from fastapi.datastructures import State

from wei.modules.rest_module import RESTModule
from wei.resources_interface import ResourceInterface
from wei.types import (
    StepFileResponse,
    StepResponse,
    StepStatus,
)
from wei.types.module_types import Location, ModuleState
from wei.types.resource_types import (
    AssetTable,
    CollectionTable,
    PlateTable,
    StackTable,
)
from wei.types.step_types import ActionRequest

# * Test predefined action functions


test_rest_node = RESTModule(
    name="test_rest_node",
    description="A test module for WEI",
    version="1.0.0",
    model="test_module",
    actions=[],
)
test_rest_node.arg_parser.add_argument(
    "--foo",
    type=float,
    help="The starting amount of foo",
    default=0.0,
)
test_rest_node.arg_parser.add_argument(
    "--bar",
    type=float,
    help="The starting amount of bar",
    default=0.0,
)


@test_rest_node.startup()
def test_node_startup(state: State):
    """Initializes the module"""
    state.foobar = state.foo + state.bar
    state.resource_interface = ResourceInterface()  # "sqlite:///test_resources.db"

    # Example: Create resources using ResourceInterface
    stack1 = StackTable(name="Stack1", description="Stack for transfer", capacity=10)
    state.resource_interface.add_resource(stack1)

    stack2 = StackTable(name="Stack2", description="Stack for transfer", capacity=10)
    state.resource_interface.add_resource(stack2)

    stack3 = StackTable(name="Stack3", description="Stack for transfer", capacity=4)
    state.resource_interface.add_resource(stack3)

    trash = StackTable(name="Trash", description="Trash", capacity=None)
    state.resource_interface.add_resource(trash)

    # Add two PlateTable resources per stack (except Trash)
    stacks = [stack1, stack2, stack3]
    for stack in stacks:
        plate1 = PlateTable(
            name=f"{stack.name} Plate1",
            description=f"Plate1 in {stack.name}",
            well_capacity=100.0,
        )
        plate2 = PlateTable(
            name=f"{stack.name} Plate2",
            description=f"Plate2 in {stack.name}",
            well_capacity=100.0,
        )

        state.resource_interface.add_resource(plate1)
        state.resource_interface.add_resource(plate2)

        # Push these plates to the stack
        state.resource_interface.push_to_stack(stack, plate1)
        state.resource_interface.push_to_stack(stack, plate2)

    plate0 = PlateTable(
        name="Plate0",
        description="Test plate",
        well_capacity=100.0,
    )
    state.resource_interface.add_resource(plate0)

    collection = CollectionTable(
        name="CollectionResource", description="Collection for measurement", capacity=5
    )
    state.resource_interface.add_resource(collection)


@test_rest_node.state_handler()
def state_handler(state: State) -> ModuleState:
    """Handles the state of the module"""
    return ModuleState(status=state.status, error=state.error, foobar=state.foobar)


@test_rest_node.action()
def transfer(
    state: State,
    action: ActionRequest,
    target: Annotated[Location[str], "the location to transfer to"],
    source: Annotated[Location[str], "the location to transfer from"] = "",
) -> StepResponse:
    """Transfers a sample from source to target"""

    if source != "":
        source_stack = state.resource_interface.get_resource(StackTable, source)
        target_stack = state.resource_interface.get_resource(StackTable, target)

        if source_stack and target_stack:
            asset = state.resource_interface.pop_from_stack(source_stack)
            state.resource_interface.push_to_stack(target_stack, asset)
            return StepResponse.step_succeeded(f"Moved asset from {source} to {target}")
        else:
            return StepResponse.step_failed(
                f"Invalid source ({source}) or target ({target}) stack"
            )

    # If no source is provided, create a new Asset and push it into the target stack
    else:
        example_plate = AssetTable(name="TestPlate")
        target_stack = state.resource_interface.get_resource(StackTable, target)

        if target_stack:
            state.resource_interface.push_to_stack(target_stack, example_plate)
            return StepResponse.step_succeeded(
                f"Created and moved 'TestPlate' to {target}"
            )
        else:
            return StepResponse.step_failed(f"Invalid target stack ({target})")


@test_rest_node.action()
def synthesize(
    state: State,
    action: ActionRequest,
    foo: Annotated[float, "The amount of foo to use"],
    bar: Annotated[float, "The amount of bar to use"],
    protocol: Annotated[UploadFile, "Python Protocol File"],
) -> StepResponse:
    """Synthesizes a sample using specified amounts `foo` and `bar` according to file `protocol`"""
    protocol = protocol.file.read().decode("utf-8")
    print(protocol)

    plate = state.resource_interface.get_resource(PlateTable, "Plate0")

    if plate:
        state.resource_interface.update_plate_well(
            plate, "A1", plate.wells.get("A1").quantity + foo
        )
        state.resource_interface.update_plate_well(
            plate, "B1", plate.wells.get("B1").quantity - bar
        )
        state.resource_interface.update_plate_contents(
            plate, {"C1": plate.well_capacity}
        )
        state.resource_interface.update_plate_well(plate, "D1", 0.0)

    return StepResponse.step_succeeded(f"Synthesized sample {foo} + {bar}")


@test_rest_node.action(name="measure")
def measure_action(state: State, action: ActionRequest) -> StepResponse:
    """Measures the foobar of the current sample"""
    collection = state.resource_interface.get_resource(
        CollectionTable, "CollectionResource"
    )

    if collection:
        print(collection.quantity)
        location = f"location_{collection.quantity + 1}"
        instance = AssetTable(name=f"Measurement at {location}")
        state.resource_interface.insert_into_collection(collection, location, instance)
        print(collection.quantity)

        with open("test.txt", "w") as f:
            f.write("test")
        return StepFileResponse(StepStatus.SUCCEEDED, "test", "test.txt")
    else:
        return StepResponse.step_failed("Collection resource not found")


if __name__ == "__main__":
    test_rest_node.start()
