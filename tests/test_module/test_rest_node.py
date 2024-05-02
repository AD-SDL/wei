"""
REST-based node that interfaces with WEI and provides various fake actions for testing purposes
"""

from fastapi.datastructures import State

from wei.modules.rest_module import RESTModule
from wei.types import ModuleAction, ModuleActionArg, ModuleActionFile, StepResponse
from wei.types.step_types import ActionRequest


def test_node_startup(state: State):
    """Initializes the module"""
    state.foobar = 0.0


# * Test Actions


def synthesize_action(state: State, action: ActionRequest) -> StepResponse:
    """Synthesizes a sample using specified amounts `foo` and `bar` according to file `protocol`"""
    foo = float(action.args["foo"])
    bar = float(action.args["bar"])
    protocol = next(file for file in action.files if file.filename == "protocol")
    protocol = protocol.file.read().decode("utf-8")
    print(protocol)

    state.foobar = foo + bar

    return StepResponse.step_succeeded("Synthesized sample {foo} + {bar}")


def measure_action(state: State, action: ActionRequest) -> StepResponse:
    """Measures the foobar of the current sample"""
    return StepResponse.step_succeeded(f"{state.foobar}")


def transfer_action(state: State, action: ActionRequest) -> StepResponse:
    """Transfers a sample from `source` to `target`"""
    source = str(action.args.get("source", None))
    target = str(action.args["target"])
    return StepResponse.step_succeeded(f"Moved sample from {source} to {target}")


test_rest_node = RESTModule(
    name="test_rest_node",
    description="A test module for WEI",
    startup_handler=test_node_startup,
    version="0.0.2",
    resource_pools=[],
    model="test_module",
    actions=[
        ModuleAction(
            name="synthesize",
            description="Synthesizes a sample",
            function=synthesize_action,
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
            function=measure_action,
            args=[],
        ),
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

test_rest_node.start()
