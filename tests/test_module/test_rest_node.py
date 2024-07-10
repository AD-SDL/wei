"""
REST-based node that interfaces with WEI and provides various fake actions for testing purposes
"""

from typing import Annotated

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

# NEED A RESOURCE DECORATOR similar to action decotor
# Initialize resources
stack_resource = StackQueue(
    information="Stack for transfer",
    name="StackResource",
    capacity=10,
    quantity=3,
    contents=[Asset(name="Plate1"), Asset(name="Plate2"), Asset(name="Plate3")],
)
pool_collection_resource = PoolCollection(
    name="Plate1",
    wells=[
        Pool(
            information=f"Well {i+1}",
            name=f"Well{i+1}",
            capacity=100.0,
            quantity=50.0,
            contents={"description": "Yellow ink", "quantity": 50.0},
        )
        for i in range(96)
    ],
)
collection_resource = Collection(
    information="Collection for measurement",
    name="CollectionResource",
    capacity=5,
    quantity=2,
)


@test_rest_node.startup()
def test_node_startup(state: State):
    """Initializes the module"""
    state.foobar = state.foo + state.bar
    state.stack_resource = stack_resource
    state.pool_resource = pool_collection_resource
    state.collection_resource = collection_resource


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
) -> StepResponse:
    """Transfers a sample from source to target"""
    print(state.stack_resource.quantity)
    print(state.stack_resource.contents)
    new_plate = Asset(name=f"Plate{len(state.stack_resource.contents) + 1}")
    state.stack_resource.push(new_plate)

    if source == "":
        print(state.stack_resource.quantity)
        print(state.stack_resource.contents)
        print("Stack resource updated")
        return StepResponse.step_succeeded(f"Moved new plate to {target}")
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
    print(state.pool_resource.quantity)
    print(state.pool_resource.contents)
    # Assume we use the first and second wells in the plate for this example
    well1 = state.pool_collection_resource.wells[0]
    well2 = state.pool_collection_resource.wells[1]
    well3 = state.pool_collection_resource.wells[2]
    well4 = state.pool_collection_resource.wells[3]
    well1.increase(foo)
    well2.decrease(bar)
    well3.fill()
    well4.empty()
    print(state.pool_collection_resource.quantity)
    print(state.pool_collection_resource.contents)

    # state.foobar = foo + bar

    return StepResponse.step_succeeded(f"Synthesized sample {foo} + {bar}")


@test_rest_node.action(name="measure")
def measure_action(state: State, action: ActionRequest) -> StepResponse:
    """Measures the foobar of the current sample"""

    print(state.collection_resource.quantity)
    print(state.collection_resource.contents)
    instance = {"measurement": state.foobar}
    location = f"location_{len(state.collection_resource.contents)+1}"
    state.collection_resource.insert(location, instance)
    print(state.collection_resource.quantity)
    print(state.collection_resource.contents)

    with open("test.txt", "w") as f:
        f.write("test")
    return StepFileResponse(StepStatus.SUCCEEDED, "test", "test.txt")


if __name__ == "__main__":
    test_rest_node.start()
