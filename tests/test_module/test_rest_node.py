"""
REST-based node that interfaces with WEI and provides various fake actions for testing purposes
"""

from time import sleep
from typing import Annotated

from fastapi import UploadFile
from fastapi.datastructures import State

from wei.modules.rest_module import RESTModule
from wei.resources_interface import ResourcesInterface
from wei.types import (
    StepResponse,
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
        state.resource_interface.delete_all_tables()
        sleep(7)
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
        state.resource_interface.update_plate_contents(
            plate0, {"A1": 50.0, "B1": 25.0, "C1": 75.0, "D1": 45.0}
        )
        collection = CollectionTable(
            name="Collection1",
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
    print("All Stacks:", all_stacks)

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

    # Read the uploaded protocol file content (not used further in this example)
    protocol_content = protocol.file.read().decode("utf-8")
    print(protocol_content)

    # Retrieve the plate resource
    plate = state.resource_interface.get_resource(
        resource_name="Plate0", module_name=state.module_name
    )

    if not plate:
        return StepResponse.step_failed("Plate0 resource not found")

    try:
        # Update specific wells
        state.resource_interface.update_plate_well(plate, "A1", 80.0)  # Set A1 to 80
        # Safely retrieve well 'B1' quantity before modification
        well_B1_quantity = state.resource_interface.get_well_quantity(plate, "B1")
        state.resource_interface.update_plate_well(
            plate, "B1", well_B1_quantity - 1
        )  # Decrease B1 by 'bar'

        # Update the entire contents of wells, setting C1 to well capacity
        state.resource_interface.update_plate_contents(
            plate, {"C1": plate.well_capacity}
        )

        # Set D1 well to zero
        state.resource_interface.update_plate_well(plate, "D1", 0.0)

        all_plates = state.resource_interface.get_all_resources(PlateTable)
        print("All Plates in the database:", all_plates)
        return StepResponse.step_succeeded()

    except Exception as e:
        return StepResponse.step_failed(f"Failed to synthesize: {e}")


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
    # Retrieve the collection resource
    collection = state.resource_interface.get_resource(
        resource_name="Collection1", module_name=state.module_name
    )

    if collection:
        print(collection.quantity)

        # Create a new location for the measurement
        location = f"location_{collection.quantity + 1}"

        # Create a new AssetTable instance
        instance = AssetTable(name=f"Measurement at {location}")

        # Insert the new asset into the collection
        state.resource_interface.insert_into_collection(collection, location, instance)

        print(f"Updated quantity: {collection.quantity}")

        # Create and write test files
        with open("test.txt", "w") as f:
            f.write("test")
        with open("test2.txt", "w") as f:
            f.write("test")

        all_collections = state.resource_interface.get_all_resources(CollectionTable)
        print("All Collections in the database:", all_collections)
        # Return the success response with the generated files
        # return StepResponse.step_succeeded(
        #     files={"test_file": "test.txt", "test2_file": "test2.txt"},
        #     data={"test": {"test": "test"}},
        # )
        return StepResponse.step_succeeded()

    else:
        return StepResponse.step_failed("Collection resource not found")


if __name__ == "__main__":
    test_rest_node.start()
