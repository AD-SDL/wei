"""
REST-based node that interfaces with WEI and provides various fake actions for testing purposes
"""

from typing import Annotated, Optional

from fastapi import UploadFile
from fastapi.datastructures import State
from wei.modules.rest_module import RESTModule
from wei.types import (
    Asset,
    Collection,
    Plate,
    Pool,
    StackResource,
    StepFileResponse,
    StepResponse,
    StepStatus,
)
from wei.types.module_types import Location, ModuleState
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


# Define and add resources
test_rest_node.add_resource(
    StackResource(
        description="Stack for transfer",
        name="Stack1",
        capacity=10,
        contents=[Asset(name="Plate1"), Asset(name="Plate2"), Asset(name="Plate3")],
    ),
)

test_rest_node.add_resource(
    StackResource(
        description="Stack for transfer",
        name="Stack2",
        capacity=10,
        contents=[],
    ),
)

test_rest_node.add_resource(
    StackResource(
        description="Stack for transfer",
        name="Stack3",
        capacity=1,
        contents=[],
    ),
)

test_rest_node.add_resource(
    StackResource(
        description="Trash",
        name="Trash",
        capacity=None,
        contents=[],
    ),
)

test_rest_node.add_resource(
    Plate(
        name="Plate1",
        contents={
            f"{row}{col}": Pool(
                description=f"Well {row}{col}",
                name=f"Well{row}{col}",
                capacity=100.0,
                quantity=50.0,
            )
            for row in "ABCDEFGH"
            for col in range(1, 13)
        },
    ),
)

test_rest_node.add_resource(
    Collection(
        description="Collection for measurement",
        name="CollectionResource",
        capacity=5,
        quantity=2,
    ),
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
def transfer(
    state: State,
    action: ActionRequest,
    target: Annotated[Location[str], "the location to transfer to"],
    source: Annotated[Location[str], "the location to transfer from"] = "",
    plate_name: Optional[str] = None,
) -> StepResponse:
    """Transfers a sample from source to target"""

    if source:
        print(state.resources[source])
        asset = state.resources[source].pop()
        print(state.resources[source])
        if plate_name:
            asset.name = plate_name
    else:
        asset = Asset(name=plate_name) if plate_name else Asset()
    print(state.resources[target])
    state.resources[target].push(asset)
    print(state.resources[target])
    return StepResponse.step_succeeded(f"Moved plate from {source} to {target}")


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

    state.resources["Plate1"].wells["A1"].increase(foo)
    state.resources["Plate1"].wells["B1"].decrease(bar)
    state.resources["Plate1"].wells["C1"].fill()
    state.resources["Plate1"].wells["D1"].empty()

    new_plate_contents = {
        "A2": 10.0,
        "B2": 20.0,
        "C2": 30.0,
        "D2": 40.0,
    }
    state.resources["Plate1"].update_plate(new_plate_contents)
    print(state.resources)

    return StepResponse.step_succeeded(f"Synthesized sample {foo} + {bar}")


@test_rest_node.action(name="measure")
def measure_action(state: State, action: ActionRequest) -> StepResponse:
    """Measures the foobar of the current sample"""

    print(state.resources["CollectionResource"].quantity)
    print(state.resources["CollectionResource"].contents)
    instance = {"measurement": state.foobar}
    location = f"location_{len(state.resources['CollectionResource'].contents) + 1}"
    state.resources["CollectionResource"].insert(location, instance)
    print(state.resources["CollectionResource"].quantity)
    print(state.resources["CollectionResource"].contents)

    with open("test.txt", "w") as f:
        f.write("test")
    return StepFileResponse(StepStatus.SUCCEEDED, "test", "test.txt")


if __name__ == "__main__":
    test_rest_node.start()
