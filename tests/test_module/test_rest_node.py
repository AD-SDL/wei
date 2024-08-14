"""
REST-based node that interfaces with WEI and provides various fake actions for testing purposes
"""

from typing import Annotated
import time

from fastapi import UploadFile
from fastapi.datastructures import State
from wei.modules.rest_module import RESTModule
from wei.types import StepFileResponse, StepResponse, StepStatus
from wei.types.module_types import (
    LocalFileModuleActionResult,
    Location,
    ModuleState,
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
    state.action_paused = False


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
    return StepResponse.step_succeeded()


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

    state.foobar = foo + bar

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
    with open("test.txt", "w") as f:
        f.write("test")
    with open("test2.txt", "w") as f:
        f.write("test")

    return StepFileResponse(
        StepStatus.SUCCEEDED,
        files={"test_file": "test.txt", "test2_file": "test2.txt"},
        data={"test": {"test": "test"}},
    )

@test_rest_node.action(name="run_action")
def run_action(state: State, action: ActionRequest) -> StepResponse:

    print("THIS METHOD WAS CALLED")
    print(test_rest_node._pause)
    """Tests the pause action functionality"""

    action_timer = 0

    while action_timer <= 30:  # only allow action to be active for 30 seconds
        # check that the action is not paused every second
        print(test_rest_node._pause)

        if state.action_paused == False:
            print("ACTION RUNNING")
            action_timer += 1
        else: 
            print("ACTION PAUSED")
        time.sleep(1)
    
    return StepResponse.step_succeeded("Entire action complete")

@test_rest_node.pause()
def pause_action(state: State):
    """Pauses the module action"""

    print("PAUSED!!!!!!!!!!!")
    state.action_paused = True

@test_rest_node.resume()
def resume_action(state: State): 
    """Resumes the module action"""

    print("RESUMED!!!!!!!!!!!")
    state.action_paused = False

    
    # return StepResponse.step_succeeded("Run action PAUSED")

# @test_rest_node.action(name="play_action")
# def play_action(state: State, action: ActionRequest): 
#     """Presses play on the run action"""

#     state.action_paused = False

#     return StepResponse.step_succeeded("Run action RESUMED")
    


    


if __name__ == "__main__":
    test_rest_node.start()
