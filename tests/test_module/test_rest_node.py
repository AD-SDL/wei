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
from wei.types.step_types import ActionRequest

# * Test predefined action functions


test_rest_node = RESTModule(
    name="test_rest_node",
    description="A test module for WEI",
    version="1.0.0",
    resource_pools=[],
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


@test_rest_node.startup()
def test_node_startup(state: State):
    """Initializes the module"""
    state.foobar = state.foo + state.bar


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
        while state.status == ModuleStatus.PAUSED:
            time.sleep(1)
        if state.status == ModuleStatus.CANCELLED:
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
    if sleep_with_signals(5, state):
        return StepResponse.step_succeeded()
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
    if not sleep_with_signals(2, state):
        return StepResponse.step_failed("Synthesis was cancelled or e-stopped.")
    protocol = protocol.file.read().decode("utf-8")
    print(protocol)

    state.foobar = foo + bar
    if sleep_with_signals(2, state):
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
    if not sleep_with_signals(2, state):
        return StepResponse.step_failed("Measure was cancelled or e-stopped.")
    with open("test.txt", "w") as f:
        f.write("test")
    with open("test2.txt", "w") as f:
        f.write("test")
    start = time.time()
    while time.time() - start < 5 and state.status == ModuleStatus.BUSY:
        time.sleep(0.1)
    if sleep_with_signals(2, state):
        return StepFileResponse(
            StepStatus.SUCCEEDED,
            files={"test_file": "test.txt", "test2_file": "test2.txt"},
            data={"test": {"test": "test"}},
        )
    else:
        return StepResponse.step_failed("Measure was cancelled or e-stopped.")


@test_rest_node.action(name="admin_actions_test")
def run_action(state: State, action: ActionRequest) -> StepResponse:
    """Allows testing of the admin action functionality"""

    action_timer = 0

    while action_timer <= 30:  # only allow action to be active for 30 seconds
        print("ACTION IS RUNNING")
        print(state.status)

        # check if the action has been safety stopped
        if state.status == ModuleStatus.CANCELLED:
            print("ACTION HAS BEEN STOPPED")
            break
        # check that the action is not paused every second
        elif state.status == ModuleStatus.PAUSED:
            action_timer += 1

        time.sleep(1)

    if state.status == ModuleStatus.CANCELLED:
        return StepResponse.step_failed()
    else:
        return StepResponse.step_succeeded()


if __name__ == "__main__":
    test_rest_node.start()
