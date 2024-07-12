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


@test_rest_node.startup()
def test_node_startup(state: State):
    """Initializes the module"""
    state.foobar = state.foo + state.bar
    # Initialize resources
    state.stack_resource = StackQueue(
        information="Stack for transfer",
        name="StackResource",
        capacity=10,
        quantity=3,
        contents=[Asset(name="Plate1"), Asset(name="Plate2"), Asset(name="Plate3")],
    )
    rows = "ABCDEFGH"
    columns = range(1, 13)
    wells = {
        f"{row}{col}": Pool(
            information=f"Well {row}{col}",
            name=f"Well{row}{col}",
            capacity=100.0,
            quantity=50.0,
            contents={"description": "Yellow ink", "quantity": 50.0},
        )
        for row in rows
        for col in columns
    }
    state.pool_collection_resource = PoolCollection(name="Plate1", wells=wells)
    state.collection_resource = Collection(
        information="Collection for measurement",
        name="CollectionResource",
        capacity=5,
        quantity=2,
    )


@test_rest_node.state_handler()
def state_handler(state: State) -> ModuleState:
    """Handles the state of the module"""
    return ModuleState(status=state.status, error=state.error, foobar=state.foobar)


# @test_rest_node.resources()
# def resources_handler(state: State) -> Dict[str, Any]:
#     """Handles the resources of the module"""
#     test_rest_node.print_resource_state(state)
#     return {
#         "stack_resource": {
#             "quantity": state.stack_resource.quantity,
#             "contents": [
#                 {"id": asset.id, "name": asset.name} for asset in state.stack_resource.contents
#             ]
#         },
#         "pool_collection_resource": {
#             "wells": {
#                 well_id: {
#                     "quantity": well.quantity,
#                     "contents": well.contents
#                 }
#                 for well_id, well in state.pool_collection_resource.wells.items()
#             }
#         },
#         "collection_resource": {
#             "quantity": state.collection_resource.quantity,
#             "contents": state.collection_resource.contents
#         }
#     }


@test_rest_node.action()
def transfer(
    state: State,
    action: ActionRequest,
    target: Annotated[Location[str], "the location to transfer to"],
    source: Annotated[Location[str], "the location to transfer from"] = "",
    plate_name: Optional[str] = None,
) -> StepResponse:
    """Transfers a sample from source to target"""
    stack_resource = state.stack_resource

    if source == "":
        test_rest_node._resources_handler(
            state, "stack", stack_resource, "push", name=plate_name
        )
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

    pool_collection_resource = state.pool_collection_resource

    test_rest_node._resources_handler(
        state,
        "pool_collection",
        pool_collection_resource,
        "update_well",
        well_id="A1",
        well_action="increase",
        amount=foo,
    )
    test_rest_node._resources_handler(
        state,
        "pool_collection",
        pool_collection_resource,
        "update_well",
        well_id="B1",
        well_action="decrease",
        amount=bar,
    )
    test_rest_node._resources_handler(
        state,
        "pool_collection",
        pool_collection_resource,
        "update_well",
        well_id="C1",
        well_action="fill",
    )
    test_rest_node._resources_handler(
        state,
        "pool_collection",
        pool_collection_resource,
        "update_well",
        well_id="D1",
        well_action="empty",
    )

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
