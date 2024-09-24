"""Resources Interface"""

from typing import Dict, List, Optional, Type

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


class ResourcesInterface:
    """
    Interface for managing various types of resources.

    Attributes:
        engine (sqlalchemy.engine.Engine): SQLAlchemy engine for database connection.
        session (sqlalchemy.orm.Session): SQLAlchemy session for database operations.
    """

    def __init__(
        self, database_url: str = "postgresql://postgres:rpl@localhost:5432/resources"
    ):
        """
        Initialize the ResourceInterface with a database URL.

        Args:
            database_url (str): Database connection URL.
        """
        self.engine = create_engine(database_url)
        self.session = Session(self.engine)
        SQLModel.metadata.create_all(self.engine)
        print(f"Resources Database started on: {database_url}")

    def add_resource(self, resource: SQLModel) -> SQLModel:
        """
        Add a resource to the database if it doesn't already exist,
        and link it to the AssetTable.

        Args:
            resource (SQLModel): The resource to add.

        Returns:
            SQLModel: The existing or newly added resource.
        """
        with self.session as session:
            # Check if the resource already exists by name and module_name
            resource_class = type(resource)
            existing_resource = session.exec(
                select(resource_class).where(
                    resource_class.name == resource.name,
                    resource_class.module_name == resource.module_name,
                )
            ).one_or_none()

            if existing_resource:
                print(f"Using existing resource: {existing_resource.name}")
                return existing_resource  # Return the existing resource if found

            # Add the new resource since it doesn't exist
            session.add(resource)
            session.commit()
            session.refresh(resource)

            # Automatically create and link an AssetTable entry
            if isinstance(resource, StackTable):
                asset = AssetTable(
                    name=f"{resource.name}",
                    stack_resource_id=resource.id,
                    module_name=resource.module_name,
                )
            elif isinstance(resource, PoolTable):
                asset = AssetTable(
                    name=f"{resource.name}",
                    pool_id=resource.id,
                    module_name=resource.module_name,
                )
            elif isinstance(resource, QueueTable):
                asset = AssetTable(
                    name=f"{resource.name}",
                    queue_resource_id=resource.id,
                    module_name=resource.module_name,
                )
            elif isinstance(resource, PlateTable):
                asset = AssetTable(
                    name=f"{resource.name}",
                    plate_id=resource.id,
                    module_name=resource.module_name,
                )
            elif isinstance(resource, CollectionTable):
                asset = AssetTable(
                    name=f"{resource.name}",
                    collection_id=resource.id,
                    module_name=resource.module_name,
                )
            else:
                asset = None

            if asset:
                session.add(asset)
                session.commit()
                session.refresh(asset)

            print(f"Added new resource: {resource.name}")
            return resource

    def get_resource(self, resource_name: str, module_name: str) -> Optional[SQLModel]:
        """
        Retrieve a resource from the database by its name and module_name across all resource types.

        Args:
            resource_name (str): The name of the resource to retrieve.
            module_name (str): The module name associated with the resource.

        Returns:
            Optional[SQLModel]: The resource if found, otherwise None.
        """
        with self.session as session:
            resource_classes = [
                StackTable,
                QueueTable,
                CollectionTable,
                PoolTable,
                PlateTable,
            ]

            for resource_class in resource_classes:
                resource = session.exec(
                    select(resource_class).where(
                        resource_class.name == resource_name,
                        resource_class.module_name == module_name,
                    )
                ).one_or_none()

                if resource:
                    print(
                        f"Resource found: {resource.name} in Module: {resource.module_name} (Type: {resource_class.__name__})"
                    )
                    return resource

            print(
                f"No resource found with name '{resource_name}' in Module: '{module_name}'"
            )
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

    def delete_all_tables(self):
        """
        Drop all tables associated with the SQLModel metadata from the database.
        """
        try:
            SQLModel.metadata.drop_all(self.engine)
            print("All tables have been deleted.")
        except Exception as e:
            print(f"An error occurred while deleting tables: {e}")

    def clear_all_table_records(self):
        """
        Delete all records from all tables associated with the SQLModel metadata.
        """
        with self.session as session:
            try:
                for table in reversed(SQLModel.metadata.sorted_tables):
                    session.exec(table.delete())
                session.commit()
                print("All table records have been cleared.")
            except Exception as e:
                session.rollback()
                print(f"An error occurred while clearing table records: {e}")

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
            session.refresh(pool)

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
            session.refresh(pool)

    def empty_pool(self, pool: PoolTable) -> None:
        """
        Empty the pool by setting the quantity to zero.

        Args:
            pool (PoolTable): The pool resource to empty.
        """
        with self.session as session:
            session.add(pool)  # Re-attach pool to the session
            pool.empty(session)
            session.refresh(pool)

    def fill_pool(self, pool: PoolTable) -> None:
        """
        Fill the pool by setting the quantity to its capacity.

        Args:
            pool (PoolTable): The pool resource to fill.
        """
        with self.session as session:
            session.add(pool)  # Re-attach pool to the session
            pool.fill(session)
            session.refresh(pool)

    def push_to_stack(self, stack: StackTable, asset: AssetTable) -> None:
        """
        Push an asset to the stack. Automatically adds the asset to the database if it's not already there.

        Args:
            stack (StackTable): The stack resource to push the asset onto.
            asset (AssetTable): The asset to push onto the stack.
        """
        with self.session as session:
            # Ensure both stack and asset are attached to the current session
            stack = session.merge(stack)
            asset = session.merge(asset)

            # Push the asset onto the stack and commit the transaction
            stack.push(asset, session)
            session.commit()
            session.refresh(stack)

    def pop_from_stack(self, stack: StackTable) -> AssetTable:
        """
        Pop an asset from a stack resource.

        Args:
            stack (StackTable): The stack resource to update.

        Returns:
            AssetTable: The popped asset.
        """
        with self.session as session:
            # Ensure the stack is attached to the current session
            stack = session.merge(stack)

            # Pop the asset from the stack and commit the transaction
            asset = stack.pop(session)
            session.commit()
            session.refresh(stack)

            if asset:
                return asset
            else:
                raise ValueError("The stack is empty or the asset does not exist.")

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
            session.refresh(queue)

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
        self, collection: CollectionTable, location: int, asset: AssetTable
    ) -> None:
        """
        Insert an asset into a collection resource.

        Args:
            collection (CollectionTable): The collection resource to update.
            location (int): The location within the collection to insert the asset.
            asset (AssetTable): The asset to insert.
        """
        with self.session as session:
            # Ensure the collection and asset are attached to the session
            collection = session.merge(collection)
            asset = session.merge(asset)

            # Insert the asset into the collection at the specified location
            collection.insert(location, asset, session)
            session.commit()
            session.refresh(collection)

    def retrieve_from_collection(
        self, collection: CollectionTable, location: int
    ) -> Optional[AssetTable]:
        """
        Retrieve an asset from a collection resource.

        Args:
            collection (CollectionTable): The collection resource to update.
            location (int): The location within the collection to retrieve the asset from.

        Returns:
            AssetTable: The retrieved asset.
        """
        with self.session as session:
            collection = session.merge(
                collection
            )  # Re-attach collection to the session
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
            plate.set_wells({well_id: quantity}, session)  # Use the updated set_wells
            session.commit()  # Commit the changes
            session.refresh(plate)  # Refresh the plate object to reflect changes

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
            plate.set_wells(new_contents, session)  # Use the updated set_wells
            session.commit()  # Commit the changes
            session.refresh(plate)  # Refresh the plate object to reflect changes

    def get_well_quantity(self, plate: PlateTable, well_id: str) -> Optional[float]:
        """
        Retrieve the quantity in a specific well of a plate resource.

        Args:
            plate (PlateTable): The plate resource to query.
            well_id (str): The ID of the well to retrieve the quantity for.

        Returns:
            Optional[float]: The quantity in the well, or None if the well does not exist.
        """
        with self.session as session:
            # Ensure the plate is attached to the current session
            plate = session.merge(plate)

            # Access the wells dictionary using the updated get_wells method
            wells = plate.get_wells(session)
            well = wells.get(well_id)

            if well is not None:
                return well.quantity  # Return the quantity of the well
            else:
                print(f"Well {well_id} not found in plate {plate.name}")
                return None

    def increase_well(self, plate: PlateTable, well_id: str, quantity: float) -> None:
        """
        Increase the quantity of liquid in a specific well of a plate.

        Args:
            plate (PlateTable): The plate resource to update.
            well_id (str): The well ID to increase the quantity for.
            quantity (float): The amount to increase the well quantity by.
        """
        with self.session as session:
            session.add(plate)  # Re-attach plate to the session
            plate.increase(well_id, quantity, session)  # Use the increase method
            session.commit()  # Commit the changes
            session.refresh(plate)  # Refresh the plate object to reflect changes

    def decrease_well(self, plate: PlateTable, well_id: str, quantity: float) -> None:
        """
        Decrease the quantity of liquid in a specific well of a plate.

        Args:
            plate (PlateTable): The plate resource to update.
            well_id (str): The well ID to decrease the quantity for.
            quantity (float): The amount to decrease the well quantity by.
        """
        with self.session as session:
            session.add(plate)  # Re-attach plate to the session
            plate.decrease(well_id, quantity, session)  # Use the decrease method
            session.commit()  # Commit the changes
            session.refresh(plate)  # Refresh the plate object to reflect changes

    def get_wells(self, plate: PlateTable) -> Dict[str, PoolTable]:
        """
        Retrieve the entire contents (wells) of a plate resource.

        Args:
            plate (PlateTable): The plate resource to query.

        Returns:
            Dict[str, PoolTable]: A dictionary of all wells in the plate, keyed by their well IDs.
        """
        with self.session as session:
            # Ensure the plate is attached to the current session
            plate = session.merge(plate)

            # Use the get_wells method from the PlateBase class to retrieve all wells
            wells = plate.get_wells(session)

            return wells  # Return the entire contents of the plate (all wells)


# Sample main function for testing
if __name__ == "__main__":
    resource_interface = ResourcesInterface()
    print(resource_interface.get_resource("Test Stack", "test2"))
    # resource_interface.clear_all_table_records()
    # Example usage: Create a Pool resource
    pool = PoolTable(
        name="Test Pool",
        description="A test pool",
        capacity=100.0,
        quantity=50.0,
        module_name="test1",
    )
    pool = resource_interface.add_resource(pool)
    # print("\nCreated Pool:", pool)
    all_pools = resource_interface.get_all_resources(PoolTable)
    print("\nAll Pools after modification:", all_pools)
    # Increase quantity in the Pool
    resource_interface.increase_pool_quantity(pool, 0.0)
    # print("Increased Pool Quantity:", pool)

    # Get all pools after modification
    all_pools = resource_interface.get_all_resources(PoolTable)
    print("\nAll Pools after modification:", all_pools)
    # Create a Stack resource
    stack = StackTable(
        name="Test Stack", description="A test stack", capacity=10, module_name="test2"
    )
    stack = resource_interface.add_resource(stack)
    retrieved_stack = resource_interface.get_resource(
        resource_name="Test Stack", module_name="test2"
    )
    print("Retreived_STACK:", retrieved_stack)
    # Push an asset to the Stack
    asset = AssetTable(name="Test Asset")
    asset3 = AssetTable(name="Test Asset3")

    resource_interface.push_to_stack(stack, asset)
    resource_interface.push_to_stack(stack, asset3)

    all_stacks = resource_interface.get_all_resources(StackTable)
    print("\nAll Stacks after modification:", all_stacks)

    # Pop an asset from the Stack
    popped_asset = resource_interface.pop_from_stack(stack)
    all_stacks = resource_interface.get_all_resources(StackTable)
    print("\nAll Stacks after modification:", all_stacks)

    # # Create a Queue resource
    # queue = QueueTable(
    #     name="Test Queue", description="A test queue", capacity=10, module_name="test3"
    # )
    # queue = resource_interface.add_resource(queue)

    # # Push an asset to the Queue
    # asset2 = AssetTable(name="Test Asset2")

    # resource_interface.push_to_queue(queue, asset2)
    # # resource_interface.push_to_queue(queue, asset)

    # # print("Updated Queue with Pushed Asset:", queue)
    # all_queues = resource_interface.get_all_resources(QueueTable)
    # print("\nAll Queues after modification:", all_queues)

    # # Pop an asset from the Queue
    # popped_asset_q = resource_interface.pop_from_queue(queue)
    # print("\nPopped Asset from Queue:", popped_asset_q)
    # all_queues = resource_interface.get_all_resources(QueueTable)
    # print("\nAll Queues after modification:", all_queues)
    # # Create a Collection resource
    collection = CollectionTable(
        name="Test Collection",
        description="A test collection",
        capacity=10,
        module_name="test4",
    )
    collection = resource_interface.add_resource(collection)

    # Insert an asset into the Collection
    resource_interface.insert_into_collection(collection, location=1, asset=asset3)

    # Retrieve an asset from the Collection
    retrieved_asset = resource_interface.retrieve_from_collection(
        collection, location=1
    )
    print("\nRetrieved Asset from Collection:", retrieved_asset)

    # Create a Plate resource
    plate = PlateTable(
        name="Test Plate",
        description="A test plate",
        well_capacity=100.0,
        module_name="test5",
    )
    plate = resource_interface.add_resource(plate)
    wells_to_add = {
        "A1": 50.0,  # Well A1 with 50.0 quantity
        "B1": 66.0,  # Well B1 with 30.0 quantity
    }
    resource_interface.update_plate_contents(plate, wells_to_add)

    # Retrieve all wells (the entire contents of the plate)
    all_wells = resource_interface.get_wells(plate)
    print(f"All wells in the plate: {all_wells}")

    # Increase the quantity in a well
    resource_interface.increase_well(plate, well_id="A1", quantity=20.0)

    # Decrease the quantity in a well
    resource_interface.decrease_well(plate, well_id="B1", quantity=10.0)
    new_well_to_add = {
        "C1": 70.0,  # Well C1 with 70.0 quantity
    }
    resource_interface.update_plate_contents(plate, new_well_to_add)

    # # Retrieve the updated contents
    updated_wells = resource_interface.get_wells(plate)
    print(f"Updated wells: {updated_wells}")
    resource_interface.update_plate_well(plate, well_id="A1", quantity=80.0)

    all_plates = resource_interface.get_all_resources(PlateTable)
    print("\nAll Plates after modification:", all_plates)

    # all_asset = resource_interface.get_all_resources(AssetTable)
    # print("\n Asset Table", all_asset)

    # print(resource_interface.get_resource_type(stack.id))

    # print(resource_interface.get_all_assets_with_relations())
