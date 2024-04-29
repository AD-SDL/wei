"""
REST-based node that interfaces with WEI and provides various fake actions for testing purposes
"""

from fastapi.datastructures import State

from wei.modules.rest_module import RESTModule
from wei.types import (
    ModuleAbout,
    ModuleAction,
    ModuleActionArg,
    ModuleActionFile,
    StepResponse,
)
from wei.types.step_types import ActionRequest


def initialize(state: State):
    """Initializes the module"""
    state.foobar = 0.0


def action_handler(state: State, action: ActionRequest) -> StepResponse:
    """Handles the actions for the test node"""
    if action.name == "synthesize":
        foo = float(action.args["foo"])
        bar = float(action.args["bar"])
        protocol = next(file for file in action.files if file.filename == "protocol")
        protocol = protocol.file.read().decode("utf-8")
        print(protocol)

        state.foobar = foo + bar

        return StepResponse.step_succeeded("Synthesized sample {foo} + {bar}")
    elif action.name == "measure":
        return StepResponse.step_succeeded(f"{state.foobar}")
    elif action.name == "transfer":
        source = str(action.args.get("source", None))
        target = str(action.args["target"])
        return StepResponse.step_succeeded(f"Moved sample from {source} to {target}")
    else:
        return StepResponse.step_failed(f"Action {action.name} not supported")


test_node_about = (
    ModuleAbout(
        name="test_rest_node",
        description="A test module for WEI",
        version="0.0.1",
        interface="wei_rest_node",
        resource_pools=[],
        model="test_module",
        actions=[
            ModuleAction(
                name="synthesize",
                description="Synthesizes a sample",
                args=[
                    ModuleActionArg(
                        name="foo",
                        description="How much foo to use",
                        required=True,
                        type="float",
                    ),
                    ModuleActionArg(
                        name="bar",
                        description="How much bar to use",
                        required=True,
                        type="float",
                    ),
                ],
                files=[
                    ModuleActionFile(
                        name="protocol",
                        required=True,
                        description="Python Protocol File",
                    )
                ],
            ),
            ModuleAction(
                name="measure",
                description="Measures the foobar of the current sample",
                args=[],
            ),
            ModuleAction(
                name="transfer",
                description="Synthesizes a sample",
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
    ),
)

test_rest_node = RESTModule(
    alias="test_rest_node",
    description="A test module for WEI",
    initialize=initialize,
    action_handler=action_handler,
    about=test_node_about,
)

test_rest_node.start()
