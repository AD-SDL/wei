"""
REST-based node that interfaces with WEI and provides various fake actions for testing purposes
"""

from typing import Annotated

from fastapi import UploadFile
from fastapi.datastructures import State

from wei.modules.rest_module import RESTModule
from wei.resources_interface import ResourcesInterface
from wei.types import (
    StepFileResponse,
    StepResponse,
    StepStatus,
)
from wei.types.module_types import (
    LocalFileModuleActionResult,
    Location,
    ModuleState,
    ValueModuleActionResult,
)
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

test_rest_node.arg_parser.add_argument(
    "--module_name",
    type=str,
    help="The starting amount of bar",
    default="test",
)


@test_rest_node.startup()
def test_node_startup(state: State):
    """Initializes the module"""
    state.foobar = state.foo + state.bar
    state.resource_interface = ResourcesInterface(
        "postgresql://rpl:rpl@wei_postgres:5432/resources"
    )
    try:
        # state.resource_interface.delete_all_tables()
        # sleep(5)
        # Example: Create resources using ResourceInterface
        stack1 = StackTable(
            name="Stack1",
            description="Stack for transfer",
            capacity=10,
            module_name=state.module_name,
        )
        state.resource_interface.add_resource(stack1)

        stack2 = StackTable(
            name="Stack2",
            description="Stack for transfer",
            capacity=10,
            module_name=state.module_name,
        )
        state.resource_interface.add_resource(stack2)

        stack3 = StackTable(
            name="Stack3",
            description="Stack for transfer",
            capacity=4,
            module_name=state.module_name,
        )
        state.resource_interface.add_resource(stack3)

        trash = StackTable(
            name="Trash",
            description="Trash",
            capacity=None,
            module_name=state.module_name,
        )
        state.resource_interface.add_resource(trash)

        # Add two PlateTable resources per stack (except Trash)
        asset = AssetTable(name="Initial Asset")

        # Push assets to stacks
        state.resource_interface.push_to_stack(stack1, asset)
        # state.resource_interface.push_to_stack(stack2, asset)

        plate0 = PlateTable(
            name="Plate0",
            description="Test plate",
            well_capacity=100.0,
            module_name=state.module_name,
        )
        state.resource_interface.add_resource(plate0)

        collection = CollectionTable(
            name="CollectionResource",
            description="Collection for measurement",
            capacity=5,
            module_name=state.module_name,
        )
        state.resource_interface.add_resource(collection)

    except Exception as err:
        print(err)


@test_rest_node.state_handler()
def state_handler(state: State) -> ModuleState:
    """Handles the state of the module"""
    return ModuleState(status=state.status, error=state.error, foobar=state.foobar)


@test_rest_node.action()
def fail(state: State, action: ActionRequest) -> StepResponse:
    """Fails the current step"""
    return StepResponse.step_failed("Oh no! This step failed!")


@test_rest_node.action()
def transfer(
    state: State,
    action: ActionRequest,
    target: Annotated[Location[str], "the location to transfer to"],
    source: Annotated[Location[str], "the location to transfer from"] = "",
) -> StepResponse:
    """Transfers a sample from source to target"""
    all_stacks = state.resource_interface.get_all_resources(StackTable)
    print("\nAll Stacks:", all_stacks)

    target_stack = state.resource_interface.get_resource(
        resource_name=target, module_name=state.module_name
    )
    if not target_stack:
        return StepResponse.step_failed(f"Invalid target stack ({target})")

    if source:
        source_stack = state.resource_interface.get_resource(
            resource_name=source, module_name=state.module_name
        )
        if not source_stack:
            return StepResponse.step_failed(f"Invalid source stack ({source})")

        try:
            asset = state.resource_interface.pop_from_stack(source_stack)
            state.resource_interface.push_to_stack(target_stack, asset)
            return StepResponse.step_succeeded()
        except ValueError as e:
            return StepResponse.step_failed(str(e))
    else:
        try:
            example_plate = AssetTable(name="ExamplePlate")
            state.resource_interface.push_to_stack(target_stack, example_plate)
            return StepResponse.step_succeeded()
        except ValueError as e:
            return StepResponse.step_failed(str(e))


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

    plate = state.resource_interface.get_resource(
        resource_name="Plate0", module_name=state.module_name
    )

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

    return StepResponse.step_succeeded()


@test_rest_node.action(
    name="measure",
    results=[
        LocalFileModuleActionResult(label="test_file", description="a test file"),
        LocalFileModuleActionResult(
            label="test2_file", description="a second test file"
        ),
        ValueModuleActionResult(label="test", description="a test value result"),
    ],
)
def measure_action(state: State, action: ActionRequest) -> StepResponse:
    """Measures the foobar of the current sample"""
    collection = state.resource_interface.get_resource(
        resource_name="CollectionResource", module_name=state.module_name
    )

    if collection:
        print(collection.quantity)
        location = f"location_{collection.quantity + 1}"
        instance = AssetTable(name=f"Measurement at {location}")
        state.resource_interface.insert_into_collection(collection, location, instance)
        print(collection.quantity)

        with open("test.txt", "w") as f:
            f.write("test")
        with open("test2.txt", "w") as f:
            f.write("test")

        return StepFileResponse(
            StepStatus.SUCCEEDED,
            files={"test_file": "test.txt", "test2_file": "test2.txt"},
            data={"test": {"test": "test"}},
        )
    else:
        return StepResponse.step_failed("Collection resource not found")


if __name__ == "__main__":
    test_rest_node.start()
