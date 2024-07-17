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
    Pool,
    PoolCollection,
    StackQueue,
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
test_rest_node.state.stack_resource = StackQueue(
    information="Stack for transfer",
    name="StackResource",
    capacity=10,
    quantity=3,
    contents=[Asset(name="Plate1"), Asset(name="Plate2"), Asset(name="Plate3")],
)
test_rest_node.resources.append(test_rest_node.state.stack_resource)

test_rest_node.state.pool_collection_resource = PoolCollection(
    name="Plate1",
    wells={
        f"{row}{col}": Pool(
            information=f"Well {row}{col}",
            name=f"Well{row}{col}",
            capacity=100.0,
            quantity=50.0,
            contents={"description": "Yellow ink", "quantity": 50.0},
        )
        for row in "ABCDEFGH"
        for col in range(1, 13)
    },
)
test_rest_node.resources.append(test_rest_node.state.pool_collection_resource)

test_rest_node.state.collection_resource = Collection(
    information="Collection for measurement",
    name="CollectionResource",
    capacity=5,
    quantity=2,
)
test_rest_node.resources.append(test_rest_node.state.collection_resource)


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
    plate_name: Optional[str] = "",
) -> StepResponse:
    """Transfers a sample from source to target"""

    asset = (
        Asset(name=plate_name)
        if plate_name
        else Asset(name=f"Plate{len(test_rest_node.resources[0].contents) + 1}")
    )
    test_rest_node.resources[0].push(asset)
    print(test_rest_node.resources)
    return StepResponse.step_succeeded(f"Moved sample from {source} to {target}")


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

    test_rest_node.resources[1].wells["A1"].increase(foo)
    test_rest_node.resources[1].wells["B1"].decrease(bar)
    test_rest_node.resources[1].wells["C1"].fill()
    test_rest_node.resources[1].wells["D1"].empty()

    new_plate_contents = {
        "A2": {"description": "Red ink", "quantity": 10.0},
        "B2": {"description": "Blue ink", "quantity": 20.0},
        "C2": {"description": "Green ink", "quantity": 30.0},
        "D2": {"description": "Yellow ink", "quantity": 40.0},
    }
    test_rest_node.resources[1].update_plate(new_plate_contents)
    print(test_rest_node.resources)

    return StepResponse.step_succeeded(f"Synthesized sample {foo} + {bar}")


@test_rest_node.action(name="measure")
def measure_action(state: State, action: ActionRequest) -> StepResponse:
    """Measures the foobar of the current sample"""

    print(test_rest_node.resources[2].quantity)
    print(test_rest_node.resources[2].contents)
    instance = {"measurement": state.foobar}
    location = f"location_{len(test_rest_node.resources[2].contents)+1}"
    test_rest_node.resources[2].insert(location, instance)
    print(test_rest_node.resources[2].quantity)
    print(test_rest_node.resources[2].contents)

    with open("test.txt", "w") as f:
        f.write("test")
    return StepFileResponse(StepStatus.SUCCEEDED, "test", "test.txt")


if __name__ == "__main__":
    test_rest_node.start()
