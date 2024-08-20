# NOQA
from resources_interface import ResourcesInterface

from wei.types.resource_types import (
    AssetTable,
    CollectionTable,
    PlateTable,
    PoolTable,
    QueueTable,
    StackTable,
)

resource_interface = ResourcesInterface()

# Example usage: Create a Pool resource
pool = PoolTable(
    name="Test Pool", description="A test pool", capacity=100.0, quantity=50.0
)
resource_interface.add_resource(pool)
# print("\nCreated Pool:", pool)
all_pools = resource_interface.get_all_resources(PoolTable)
print("\nAll Pools after modification:", all_pools)
# Increase quantity in the Pool
resource_interface.increase_pool_quantity(pool, 25.0)
# print("Increased Pool Quantity:", pool)

# Get all pools after modification
all_pools = resource_interface.get_all_resources(PoolTable)
print("\nAll Pools after modification:", all_pools)

# Create a Stack resource
stack = StackTable(name="Test Stack", description="A test stack", capacity=10)
resource_interface.add_resource(stack)
print("\nCreated Stack:", stack)

# Push an asset to the Stack
asset = AssetTable(name="Test Asset")
resource_interface.push_to_stack(stack, asset)
# print("Updated Stack with Pushed Asset:", stack)

all_stacks = resource_interface.get_all_resources(StackTable)
print("\nAll Stacks after modification:", all_stacks)

# Pop an asset from the Stack
popped_asset = resource_interface.pop_from_stack(stack)
# print("Popped Asset from Stack:", popped_asset)
all_stacks = resource_interface.get_all_resources(StackTable)
print("\nAll Stacks after modification:", all_stacks)

# Create a Queue resource
queue = QueueTable(name="Test Queue", description="A test queue", capacity=10)
resource_interface.add_resource(queue)
# print("\nCreated Queue:", queue)

# Push an asset to the Queue
resource_interface.push_to_queue(queue, asset)
# print("Updated Queue with Pushed Asset:", queue)
all_queues = resource_interface.get_all_resources(QueueTable)
print("\nAll Queues after modification:", all_queues)

# Pop an asset from the Queue
popped_asset = resource_interface.pop_from_queue(queue)
print("\nPopped Asset from Queue:", popped_asset)
all_queues = resource_interface.get_all_resources(QueueTable)
print("\nAll Queues after modification:", all_queues)
# Create a Collection resource
collection = CollectionTable(
    name="Test Collection", description="A test collection", capacity=10
)
resource_interface.add_resource(collection)
print("\nCreated Collection:", collection)

# Insert an asset into the Collection
resource_interface.insert_into_collection(collection, "location1", asset)
print("\nUpdated Collection with Inserted Asset:", collection)

# Retrieve an asset from the Collection
retrieved_asset = resource_interface.retrieve_from_collection(collection, "location1")
print("\nRetrieved Asset from Collection:", retrieved_asset)

# Create a Plate resource
plate = PlateTable(name="Test Plate", description="A test plate", well_capacity=100.0)
resource_interface.add_resource(plate)
# print("\nCreated Plate:", plate)

# Update the contents of the Plate
resource_interface.update_plate_contents(
    plate, {"A1": 75.0, "A2": 75.0, "A3": 75.0, "A4": 75.0}
)
print("\nUpdated Plate Contents:", plate)

# Update a specific well in the Plate
resource_interface.update_plate_well(plate, "A1", 80.0)
print("\nUpdated Specific Well in Plate:", plate)

all_plates = resource_interface.get_all_resources(PlateTable)
print("\nAll Plates after modification:", all_plates)

all_asset = resource_interface.get_all_resources(AssetTable)
print("\n Asset Table", all_asset)

print(resource_interface.get_resource_type(stack.id))

# print(resource_interface.get_all_assets_with_relations())


# How to use backpopulate to make sure the assets are related with across tables so I remove a asset from the AssetTable will it be removed from the corresponding resource table as well?
