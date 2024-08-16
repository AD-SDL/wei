"""Resources Interface"""

from typing import Dict, List, Optional, Type

from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import selectinload
from sqlmodel import Session, SQLModel, create_engine, select

from wei.types.resource_types import (
    AssetTable,
    CollectionTable,
    PlateTable,
    PoolTable,
    QueueTable,
    StackTable,
)


class ResourceInterface:
    """
    Interface for managing various types of resources.

    Attributes:
        engine (sqlalchemy.engine.Engine): SQLAlchemy engine for database connection.
        session (sqlalchemy.orm.Session): SQLAlchemy session for database operations.
    """

    def __init__(self, database_url: str = "sqlite:///:memory:"):
        """
        Initialize the ResourceInterface with a database URL.

        Args:
            database_url (str): Database connection URL.
        """
        self.engine = create_engine(database_url)
        self.session = Session(self.engine)
        SQLModel.metadata.create_all(self.engine)

    def add_resource(self, resource: SQLModel) -> SQLModel:
        """
        Add a resource to the database and link it to the AssetTable.

        Args:
            resource (SQLModel): The resource to add.

        Returns:
            SQLModel: The added resource.
        """
        with self.session as session:
            session.add(resource)
            session.commit()
            session.refresh(resource)

            # Automatically create and link an AssetTable entry
            if isinstance(resource, StackTable):
                asset = AssetTable(
                    name=f"Asset for {resource.name}", stack_resource_id=resource.id
                )
            elif isinstance(resource, PoolTable):
                asset = AssetTable(
                    name=f"Asset for {resource.name}", pool_id=resource.id
                )
            elif isinstance(resource, QueueTable):
                asset = AssetTable(
                    name=f"Asset for {resource.name}", queue_resource_id=resource.id
                )
            elif isinstance(resource, PlateTable):
                asset = AssetTable(
                    name=f"Asset for {resource.name}", plate_id=resource.id
                )
            elif isinstance(resource, CollectionTable):
                asset = AssetTable(
                    name=f"Asset for {resource.name}", collection_id=resource.id
                )
            else:
                asset = None

            if asset:
                session.add(asset)
                session.commit()
                session.refresh(asset)

            return resource

    def get_resource(
        self,
        resource_type: Type[SQLModel],
        resource_id: Optional[str] = None,
        resource_name: Optional[str] = None,
    ) -> Optional[SQLModel]:
        """
        Retrieve a resource from the database by ID or name.

        Args:
            resource_type (Type[SQLModel]): The type of the resource.
            resource_id (str, optional): The ID of the resource.
            resource_name (str, optional): The name of the resource.

        Returns:
            SQLModel: The retrieved resource, or None if not found.
        """
        with self.session as session:
            if resource_id:
                statement = select(resource_type).where(resource_type.id == resource_id)
            elif resource_name:
                statement = select(resource_type).where(
                    resource_type.name == resource_name
                )
            else:
                raise ValueError(
                    "Either resource_id or resource_name must be provided."
                )

            try:
                resource = session.exec(statement).one()
                return resource
            except NoResultFound:
                return None

    def get_resource_type(self, resource_id: str) -> Optional[str]:
        """
        Determine the resource type name based on the provided resource_id.

        Args:
            resource_id (str): The ID of the resource.

        Returns:
            str or None: The name of the resource type if found, otherwise None.
        """
        resource_types = {
            "StackTable": StackTable,
            "PoolTable": PoolTable,
            "QueueTable": QueueTable,
            "CollectionTable": CollectionTable,
            "PlateTable": PlateTable,
        }

        with self.session as session:
            for type_name, resource_type in resource_types.items():
                statement = select(resource_type).where(resource_type.id == resource_id)
                result = session.exec(statement).first()
                if result:
                    return type_name

        return None

    def update_resource(
        self, resource_type: Type[SQLModel], resource_id: str, updates: Dict
    ) -> Optional[SQLModel]:
        """
        Update a resource in the database.

        Args:
            resource_type (Type[SQLModel]): The type of the resource.
            resource_id (str): The ID of the resource.
            updates (Dict): The updates to apply.

        Returns:
            SQLModel: The updated resource, or None if not found.
        """
        with self.session as session:
            resource = self.get_resource(resource_type, resource_id)
            if not resource:
                return None

            for key, value in updates.items():
                setattr(resource, key, value)

            session.add(resource)
            session.commit()
            session.refresh(resource)
            return resource

    def delete_resource(self, resource_type: Type[SQLModel], resource_id: str) -> bool:
        """
        Delete a resource from the database.

        Args:
            resource_type (Type[SQLModel]): The type of the resource.
            resource_id (str): The ID of the resource.

        Returns:
            bool: True if the resource was deleted, False if not found.
        """
        with self.session as session:
            resource = self.get_resource(resource_type, resource_id)
            if not resource:
                return False

            session.delete(resource)
            session.commit()
            return True

    def get_all_resources(self, resource_type: Type[SQLModel]) -> List[SQLModel]:
        """
        Retrieve all resources of a specific type from the database.

        Args:
            resource_type (Type[SQLModel]): The type of the resources.

        Returns:
            List[SQLModel]: A list of all resources of the specified type.
        """
        with self.session as session:
            statement = select(resource_type)
            # If the resource type is AssetTable, load all relationships
            if resource_type is AssetTable:
                statement = statement.options(
                    selectinload(AssetTable.stack),
                    selectinload(AssetTable.queue),
                    selectinload(AssetTable.pool),
                    selectinload(AssetTable.collection),
                    selectinload(AssetTable.plate),
                )
            resources = session.exec(statement).all()
            return resources

    # Methods to delegate resource operations
    def increase_pool_quantity(self, pool: PoolTable, amount: float) -> None:
        """
        Increase the quantity of a pool resource.

        Args:
            pool (PoolTable): The pool resource to update.
            amount (float): The amount to increase.
        """
        with self.session as session:
            session.add(pool)  # Re-attach pool to the session
            pool.increase(amount, session)

    def decrease_pool_quantity(self, pool: PoolTable, amount: float) -> None:
        """
        Decrease the quantity of a pool resource.

        Args:
            pool (PoolTable): The pool resource to update.
            amount (float): The amount to decrease.
        """
        with self.session as session:
            session.add(pool)  # Re-attach pool to the session
            pool.decrease(amount, session)

    def empty_pool(self, pool: PoolTable) -> None:
        """
        Empty the pool by setting the quantity to zero.

        Args:
            pool (PoolTable): The pool resource to empty.
        """
        with self.session as session:
            session.add(pool)  # Re-attach pool to the session
            pool.empty(session)

    def fill_pool(self, pool: PoolTable) -> None:
        """
        Fill the pool by setting the quantity to its capacity.

        Args:
            pool (PoolTable): The pool resource to fill.
        """
        with self.session as session:
            session.add(pool)  # Re-attach pool to the session
            pool.fill(session)

    def push_to_stack(self, stack: StackTable, asset: AssetTable) -> None:
        """
        Push an asset to the stack. Automatically adds the asset to the database if it's not already there.

        Args:
            stack (StackTable): The stack resource to push the asset onto.
            asset (AssetTable): The asset to push onto the stack.
        """
        with self.session as session:
            session.add(stack)  # Re-attach stack to the session

            # Check if asset exists in the database
            existing_asset = session.get(AssetTable, asset.id)
            if not existing_asset:
                session.add(asset)
                session.commit()
                session.refresh(asset)
            else:
                session.add(
                    existing_asset
                )  # Re-attach the existing asset to the session

            # Now push the asset onto the stack
            stack.push(asset, session)
            session.commit()

    def pop_from_stack(self, stack: StackTable) -> AssetTable:
        """
        Pop an asset from a stack resource.

        Args:
            stack (StackTable): The stack resource to update.

        Returns:
            AssetTable: The popped asset.
        """
        with self.session as session:
            session.add(stack)  # Re-attach stack to the session
            return stack.pop(session)

    def push_to_queue(self, queue: QueueTable, asset: AssetTable) -> None:
        """
        Push an asset to the queue. Automatically adds the asset to the database if it's not already there.

        Args:
            queue (QueueTable): The queue resource to push the asset onto.
            asset (AssetTable): The asset to push onto the queue.
        """
        with self.session as session:
            session.add(queue)  # Re-attach queue to the session

            # Ensure the asset is attached to the session
            asset = session.merge(asset)

            # Check if the asset exists in the database
            existing_asset = session.get(AssetTable, asset.id)
            if not existing_asset:
                session.add(asset)
                session.commit()
                session.refresh(asset)

            # Now push the asset onto the queue
            queue.push(asset, session)
            session.commit()

    def pop_from_queue(self, queue: QueueTable) -> AssetTable:
        """
        Pop an asset from a queue resource.

        Args:
            queue (QueueTable): The queue resource to update.

        Returns:
            AssetTable: The popped asset.
        """
        with self.session as session:
            session.add(queue)  # Re-attach queue to the session
            return queue.pop(session)

    def insert_into_collection(
        self, collection: CollectionTable, location: str, asset: AssetTable
    ) -> None:
        """
        Insert an asset into a collection resource.

        Args:
            collection (CollectionTable): The collection resource to update.
            location (str): The location within the collection to insert the asset.
            asset (AssetTable): The asset to insert.
        """
        with self.session as session:
            session.add(collection)  # Re-attach collection to the session
            session.add(asset)  # Re-attach asset to the session
            collection.insert(location, asset, session)
            session.commit()
            print(
                f"Updated Collection Contents after insertion: {collection.collection_contents}"
            )

    def retrieve_from_collection(
        self, collection: CollectionTable, location: str
    ) -> Optional[AssetTable]:
        """
        Retrieve an asset from a collection resource.

        Args:
            collection (CollectionTable): The collection resource to update.
            location (str): The location within the collection to retrieve the asset from.

        Returns:
            AssetTable: The retrieved asset.
        """
        with self.session as session:
            session.add(collection)  # Re-attach collection to the session
            print(
                f"Collection contents before retrieval: {collection.collection_contents}"
            )
            return collection.retrieve(
                location, session
            )  # Ensure the correct order of arguments

    def update_plate_well(
        self, plate: PlateTable, well_id: str, quantity: float
    ) -> None:
        """
        Update the quantity of a specific well in a plate resource.

        Args:
            plate (PlateTable): The plate resource to update.
            well_id (str): The well ID to update.
            quantity (float): The new quantity for the well.
        """
        with self.session as session:
            session.add(plate)  # Re-attach plate to the session
            plate.update_well(well_id, quantity, session)

    def update_plate_contents(
        self, plate: PlateTable, new_contents: Dict[str, float]
    ) -> None:
        """
        Update the entire contents of a plate resource.

        Args:
            plate (PlateTable): The plate resource to update.
            new_contents (Dict[str, float]): A dictionary with well IDs as keys and quantities as values.
        """
        with self.session as session:
            session.add(plate)  # Re-attach plate to the session
            plate.update_plate(new_contents, session)


# Sample main function for testing
if __name__ == "__main__":
    resource_interface = ResourceInterface()

    # Example usage: Create a Pool resource
    pool = PoolTable(
        name="Test Pool", description="A test pool", capacity=100.0, quantity=50.0
    )
    resource_interface.add_resource(pool)
    print("\nCreated Pool:", pool)

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
    print("\nCreated Queue:", queue)

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
    retrieved_asset = resource_interface.retrieve_from_collection(
        collection, "location1"
    )
    print("\nRetrieved Asset from Collection:", retrieved_asset)

    # Create a Plate resource
    plate = PlateTable(
        name="Test Plate", description="A test plate", well_capacity=100.0
    )
    resource_interface.add_resource(plate)
    print("\nCreated Plate:", plate)

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
