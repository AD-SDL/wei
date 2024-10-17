"""
REST-based node that interfaces with WEI and provides various fake actions for testing purposes
"""

import time
from typing import Annotated

from fastapi import UploadFile
from fastapi.datastructures import State

from wei.modules.rest_module import RESTModule
from wei.types import StepFileResponse, StepResponse, StepStatus
from wei.types.module_types import (
    AdminCommands,
    LocalFileModuleActionResult,
    Location,
    ModuleState,
    ModuleStatus,
    ValueModuleActionResult,
)
from wei.types.resource_types import Asset, Collection, Plate, Stack
from wei.types.step_types import ActionRequest

# * Test predefined action functions


test_rest_node = RESTModule(
    name="test_rest_node",
    description="A test module for WEI",
    version="1.0.0",
    model="test_module",
    actions=[],
    admin_commands=set([admin_command for admin_command in AdminCommands]),
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
    "--dwell_time", type=int, help="The amount of time to dwell on actions", default=1
)


@test_rest_node.startup()
def test_node_startup(state: State):
    """Initializes the module"""
    state.foobar = state.foo + state.bar
    try:
        # Example: Create resources using ResourceInterface
        stack1 = Stack(
            name="Stack1",
            description="Stack for transfer",
            capacity=10,
            owner_name=state.name,
        )
        stack1 = state.resources_interface.add_resource(stack1)
        stack2 = Stack(
            name="Stack2",
            description="Stack for transfer",
            capacity=10,
            owner_name=state.name,
        )
        stack2 = state.resources_interface.add_resource(stack2)

        stack3 = Stack(
            name="Stack3",
            description="Stack for transfer",
            capacity=4,
            owner_name=state.name,
        )
        stack3 = state.resources_interface.add_resource(stack3)

        trash = Stack(
            name="Trash",
            description="Trash",
            capacity=None,
            owner_name=state.name,
        )
        trash = state.resources_interface.add_resource(trash)

        asset = Asset(name="Initial Asset")

        # Push assets to stacks
        state.resources_interface.push_to_stack(stack1, asset)

        plate0 = Plate(
            name="Plate0",
            description="Test plate",
            well_capacity=100.0,
            owner_name=state.name,
        )
        plate0 = state.resources_interface.add_resource(plate0)
        state.resources_interface.update_plate_contents(
            plate0, {"A1": 50.0, "B1": 25.0, "C1": 75.0, "D1": 45.0}
        )
        collection = Collection(
            name="Collection1",
            description="Collection for measurement",
            capacity=5,
            owner_name=state.name,
        )
        collection = state.resources_interface.add_resource(collection)

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


def sleep_with_signals(seconds: int, state: State):
    """Sleeps for `seconds` seconds, checking for state changes every second"""
    for i in range(seconds):
        print(i)
        time.sleep(1)
        while state.status[ModuleStatus.PAUSED]:
            time.sleep(1)
        if (
            state.status[ModuleStatus.PAUSED]
            or state.status[ModuleStatus.CANCELLED]
            or state.status[ModuleStatus.INIT]
        ):
            return False
    return True


@test_rest_node.action()
def transfer(
    state: State,
    action: ActionRequest,
    target: Annotated[Location[str], "the location to transfer to"],
    source: Annotated[Location[str], "the location to transfer from"] = "",
) -> StepResponse:
    """Transfers a sample from source to target"""
    all_stacks = state.resources_interface.get_all_resources(Stack)
    print("All Stacks:", all_stacks)

    target_stack = state.resources_interface.get_resource(
        resource_name=target, owner_name=state.name
    )
    if not target_stack:
        return StepResponse.step_failed(f"Invalid target stack ({target})")

    if sleep_with_signals(state.dwell_time, state):
        if source:
            source_stack = state.resources_interface.get_resource(
                resource_name=source, owner_name=state.name
            )
            if not source_stack:
                return StepResponse.step_failed(f"Invalid source stack ({source})")

            try:
                asset = state.resources_interface.pop_from_stack(source_stack)
                state.resources_interface.push_to_stack(target_stack, asset)
                return StepResponse.step_succeeded()
            except ValueError as e:
                return StepResponse.step_failed(str(e))
        else:
            try:
                example_plate = Asset(name="ExamplePlate")
                state.resources_interface.push_to_stack(target_stack, example_plate)
                return StepResponse.step_succeeded()
            except ValueError as e:
                return StepResponse.step_failed(str(e))
    else:
        return StepResponse.step_failed("Transfer was cancelled or e-stopped.")


@test_rest_node.action()
def synthesize(
    state: State,
    action: ActionRequest,
    foo: Annotated[float, "The amount of foo to use"],
    bar: Annotated[float, "The amount of bar to use"],
    protocol: Annotated[UploadFile, "Python Protocol File"],
) -> StepResponse:
    """Synthesizes a sample using specified amounts `foo` and `bar` according to file `protocol`"""
    if not sleep_with_signals(state.dwell_time, state):
        return StepResponse.step_failed("Synthesis was cancelled or e-stopped.")
    protocol = protocol.file.read().decode("utf-8")
    print(protocol)

    state.foobar = foo + bar
    if sleep_with_signals(state.dwell_time, state):
        return StepResponse.step_succeeded()
    else:
        return StepResponse.step_failed("Synthesis was cancelled or e-stopped.")


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
    if not sleep_with_signals(state.dwell_time, state):
        return StepResponse.step_failed("Measure was cancelled or e-stopped.")
    # Retrieve the collection resource
    collection = state.resources_interface.get_resource(
        resource_name="Collection1", owner_name=state.name
    )

    if collection:
        print(collection.quantity)

        # Create a new location for the measurement
        location = f"location_{collection.quantity + 1}"
        # Create a new Asset instance
        instance = Asset(name=f"Measurement at {location}")
        # Insert the new asset into the collection
        state.resources_interface.insert_into_collection(collection, location, instance)

        print(f"Updated quantity: {collection.quantity}")

        with open("test.txt", "w") as f:
            f.write("test")
        with open("test2.txt", "w") as f:
            f.write("test")
        if sleep_with_signals(state.dwell_time, state):
            return StepFileResponse(
                StepStatus.SUCCEEDED,
                files={"test_file": "test.txt", "test2_file": "test2.txt"},
                data={"test": {"test": "test"}},
            )
    else:
        return StepResponse.step_failed("Collection resource not found")


@test_rest_node.action(name="admin_actions_test")
def admin_actions_test(state: State, action: ActionRequest) -> StepResponse:
    """Allows testing of the admin action functionality"""

    if not sleep_with_signals(30, state):
        return StepResponse.step_failed()
    else:
        return StepResponse.step_succeeded()


if __name__ == "__main__":
    test_rest_node.start()
