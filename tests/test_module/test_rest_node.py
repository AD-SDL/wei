"""
REST-based node that interfaces with WEI and provides various fake actions for testing purposes
"""

from typing import Annotated

from fastapi import UploadFile
from fastapi.datastructures import State

from wei.modules.rest_module import RESTModule
from wei.types import ModuleAction, ModuleActionArg, StepResponse, StepStatus, StepFileResponse
from wei.types.module_types import ModuleState
from wei.types.step_types import ActionRequest


# * Test predefined action functions
def transfer_action(state: State, action: ActionRequest) -> StepResponse:
    """Transfers a sample from `source` to `target`"""
    source = str(action.args.get("source", None))
    target = str(action.args["target"])
    return StepResponse.step_succeeded(f"Moved sample from {source} to {target}")


test_rest_node = RESTModule(
    name="test_rest_node",
    description="A test module for WEI",
    version="1.0.0",
    resource_pools=[],
    model="test_module",
    actions=[
        ModuleAction(
            name="transfer",
            description="Synthesizes a sample",
            function=transfer_action,
            args=[
                ModuleActionArg(
                    name="source",
                    description="Location to transfer sample from",
                    required=False,
                    type="Location",
                    default="[0, 0, 0, 0, 0, 0, 0]",
                ),
                ModuleActionArg(
                    name="target",
                    description="Location to transfer sample to",
                    required=True,
                    type="Location",
                ),
            ],
        ),
    ],
)


@test_rest_node.startup()
def test_node_startup(state: State):
    """Initializes the module"""
    state.foobar = 0.0


@test_rest_node.state_handler()
def state_handler(state: State) -> ModuleState:
    """Handles the state of the module"""
    return ModuleState(status=state.status, error=state.error, foobar=state.foobar)


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

    return StepResponse.step_succeeded("Synthesized sample {foo} + {bar}")


@test_rest_node.action(name="measure")
def measure_action(state: State, action: ActionRequest) -> StepResponse:
    """Measures the foobar of the current sample"""
    with open("test.txt", 'w') as f:
        f.write("test")
    return StepFileResponse(StepStatus.SUCCEEDED, "test", "test.txt")


test_rest_node.start()
