"""Resources Interface"""

from typing import Dict, List, Optional, Type

from sqlalchemy import text
from sqlalchemy.exc import MultipleResultsFound
from sqlmodel import Session, SQLModel, create_engine, select

from wei.types.resource_types import (
    Asset,
    Collection,
    Plate,
    Pool,
    Queue,
    ResourceContainerBase,
    Stack,
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

    def add_resource(self, resource: ResourceContainerBase):
        """
        Add a resource to the database using the add_resource method
        in ResourceContainerBase.

        Args:
            resource (ResourceContainerBase): The resource to add.

        Returns:
            ResourceContainerBase: The saved or existing resource.
        """
        with self.session as session:
            return resource.add_resource(session)

    def get_resource(
        self,
        resource_name: Optional[str] = None,
        owner_name: Optional[str] = None,
        resource_id: Optional[str] = None,
    ) -> Optional[SQLModel]:
        """
        Retrieve a resource from the database by its name and owner_name across all resource types.

        Args:
            resource_name (str): The name of the resource to retrieve.
            owner_name (str): The module name associated with the resource.
            resource_id (Optional[str]): The optional ID of the resource (if provided, this will take priority).

        Returns:
            Optional[SQLModel]: The resource if found, otherwise None.
        """
        if not resource_id and (not resource_name or not owner_name):
            raise ValueError(
                "You must provide either a resource_id or both resource_name and owner_name."
            )

        with self.session as session:
            resource_classes = [
                Stack,
                Queue,
                Collection,
                Pool,
            ]

        # If resource_id is provided, use it to directly query the resource
        if resource_id:
            for resource_class in resource_classes:
                statement = select(resource_class).where(
                    resource_class.id == resource_id
                )
                resource = session.exec(statement).first()

                if resource:
                    # Check if the resource is a Collection and is_plate is True
                    if isinstance(resource, Collection) and resource.is_plate:
                        plate = Plate(
                            id=resource.id,
                            name=resource.name,
                            description=resource.description,
                            capacity=resource.capacity,
                            well_capacity=100.0,  # TODO: Set well_capacity dynamically
                            owner_name=resource.owner_name,
                            quantity=resource.quantity,
                            unique_resource=resource.unique_resource,
                        )
                        return plate

                    # If it's not a plate, return the found resource
                    print(f"Resource found by ID: {resource.id}")
                    return resource

            print(f"No resource found with ID '{resource_id}'.")
            return None

        # Fallback to using resource_name and owner_name if resource_id is not provided
        for resource_class in resource_classes:
            statement = select(resource_class).where(
                resource_class.name == resource_name,
                resource_class.owner_name == owner_name,
            )
            resources = session.exec(statement).all()
            if not resources:
                continue

            # Handle multiple results found
            if len(resources) > 1:
                raise MultipleResultsFound(
                    f"Multiple resources found for name '{resource_name}' in owner '{owner_name}'. Please provide a resource ID."
                )

            resource = resources[0]

            # If the resource is a Plate (Collection with is_plate=True), return a Plate object
            if isinstance(resource, Collection) and resource.is_plate:
                plate = Plate(
                    id=resource.id,
                    name=resource.name,
                    description=resource.description,
                    capacity=resource.capacity,
                    well_capacity=100.0,  # TODO: Set well_capacity dynamically
                    owner_name=resource.owner_name,
                    quantity=resource.quantity,
                    unique_resource=resource.unique_resource,
                )
                return plate

            print(
                f"Resource found: {resource.name} in owner '{owner_name}' (Type: {resource_class.__name__})"
            )
            return resource

        print(f"No resource found with name '{resource_name}' in owner '{owner_name}'.")
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
            "Stack": Stack,
            "Pool": Pool,
            "Queue": Queue,
            "Collection": Collection,
            "Plate": Plate,
        }

        with self.session as session:
            for type_name, resource_type in resource_types.items():
                statement = select(resource_type).where(resource_type.id == resource_id)
                result = session.exec(statement).first()
                if result:
                    return type_name

        return None

    def get_all_resources(self, resource_type: Type[SQLModel]) -> List[SQLModel]:
        """
        Retrieve all resources of a specific type from the database.

        Args:
            resource_type (Type[SQLModel]): The type of the resources.

        Returns:
            List[SQLModel]: A list of all resources of the specified type.
        """
        with self.session as session:
            # Handle Plate type by filtering Collection where is_plate=True
            if resource_type is Plate:
                statement = select(Collection).where(Collection.is_plate)
                resources = session.exec(statement).all()
                return resources

            # Handle Collection type by filtering Collection where is_plate=False
            elif resource_type is Collection:
                statement = select(Collection).where(Collection.is_plate)
                resources = session.exec(statement).all()
                return resources

            # Handle all other resource types normally
            else:
                statement = select(resource_type)
                # Fetch and return resources of the requested type
                resources = session.exec(statement).all()
                return resources

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
            with self.engine.connect() as connection:
                # Drop Asset first, handling foreign key constraints with CASCADE
                connection.execute(text("DROP TABLE IF EXISTS assetallocation CASCADE"))
                connection.commit()
            # Drop the rest of the tables
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

    def increase_pool_quantity(self, pool: Pool, amount: float) -> None:
        """
        Increase the quantity of a pool resource.

        Args:
            pool (Pool): The pool resource to update.
            amount (float): The amount to increase.
        """
        with self.session as session:
            session.add(pool)
            pool.increase(amount, session)
            session.refresh(pool)

    def decrease_pool_quantity(self, pool: Pool, amount: float) -> None:
        """
        Decrease the quantity of a pool resource.

        Args:
            pool (Pool): The pool resource to update.
            amount (float): The amount to decrease.
        """
        with self.session as session:
            session.add(pool)
            pool.decrease(amount, session)
            session.refresh(pool)

    def empty_pool(self, pool: Pool) -> None:
        """
        Empty the pool by setting the quantity to zero.

        Args:
            pool (Pool): The pool resource to empty.
        """
        with self.session as session:
            session.add(pool)
            pool.empty(session)
            session.refresh(pool)

    def fill_pool(self, pool: Pool) -> None:
        """
        Fill the pool by setting the quantity to its capacity.

        Args:
            pool (Pool): The pool resource to fill.
        """
        with self.session as session:
            session.add(pool)
            pool.fill(session)
            session.refresh(pool)

    def push_to_stack(self, stack: Stack, asset: Asset) -> None:
        """
        Push an asset to the stack. Automatically adds the asset to the database if it's not already there.

        Args:
            stack (Stack): The stack resource to push the asset onto.
            asset (Asset): The asset to push onto the stack.
        """
        with self.session as session:
            stack = session.merge(stack)
            asset = session.merge(asset)
            stack.push(asset, session)
            session.commit()
            session.refresh(stack)

    def pop_from_stack(self, stack: Stack) -> Asset:
        """
        Pop an asset from a stack resource.

        Args:
            stack (Stack): The stack resource to update.

        Returns:
            Asset: The popped asset.
        """
        with self.session as session:
            stack = session.merge(stack)
            asset = stack.pop(session)
            session.commit()
            session.refresh(stack)

            if asset:
                return asset
            else:
                raise ValueError("The stack is empty or the asset does not exist.")

    def push_to_queue(self, queue: Queue, asset: Asset) -> None:
        """
        Push an asset to the queue. Automatically adds the asset to the database if it's not already there.

        Args:
            queue (Queue): The queue resource to push the asset onto.
            asset (Asset): The asset to push onto the queue.
        """
        with self.session as session:
            session.add(queue)
            asset = session.merge(asset)
            existing_asset = session.get(Asset, asset.id)
            if not existing_asset:
                session.add(asset)
                session.commit()
                session.refresh(asset)

            queue.push(asset, session)
            session.commit()
            session.refresh(queue)

    def pop_from_queue(self, queue: Queue) -> Asset:
        """
        Pop an asset from a queue resource.

        Args:
            queue (Queue): The queue resource to update.

        Returns:
            Asset: The popped asset.
        """
        with self.session as session:
            session.add(queue)
            return queue.pop(session)

    def insert_into_collection(
        self, collection: Collection, location: str, asset: Asset
    ) -> None:
        """
        Insert an asset into a collection resource.

        Args:
            collection (Collection): The collection resource to update.
            location (str): The location within the collection to insert the asset.
            asset (Asset): The asset to insert.
        """
        with self.session as session:
            collection = session.merge(collection)
            asset = session.merge(asset)
            collection.insert(location, asset, session)
            session.commit()
            session.refresh(collection)

    def retrieve_from_collection(
        self, collection: Collection, location: str
    ) -> Optional[Asset]:
        """
        Retrieve an asset from a collection resource.

        Args:
            collection (Collection): The collection resource to update.
            location (str): The location within the collection to retrieve the asset from.

        Returns:
            Asset: The retrieved asset.
        """
        with self.session as session:
            collection = session.merge(collection)
            return collection.retrieve(location, session)

    def update_plate_well(self, plate: Plate, well_id: str, quantity: float) -> None:
        """
        Update the quantity of a specific well in a plate resource.

        Args:
            plate (Plate): The plate resource to update.
            well_id (str): The well ID to update.
            quantity (float): The new quantity for the well.
        """
        with self.session as session:
            # Find the corresponding collection (plate) in the database
            collection = session.query(Collection).filter_by(name=plate.name).first()

            if not collection:
                raise ValueError(f"Collection for plate {plate.name} not found.")

            # Use the set_wells function to update the well quantity
            plate.set_wells({well_id: quantity}, session)

            # Commit the changes and refresh the collection object if needed
            session.commit()
            session.refresh(collection)

    def update_plate_contents(
        self, plate: Plate, new_contents: Dict[str, float]
    ) -> None:
        """
        Update the entire contents of a plate resource.

        Args:
            plate (Plate): The plate resource to update.
            new_contents (Dict[str, float]): A dictionary with well IDs as keys and quantities as values.
        """
        with self.session as session:
            # Retrieve the corresponding Collection from the database
            collection = (
                session.query(Collection)
                .filter_by(
                    name=plate.name,
                    owner_name=plate.owner_name,
                )
                .first()
            )

            if not collection:
                raise ValueError(f"Collection for Plate {plate.name} not found.")

            # Use the plate object (in memory) to update the wells
            plate.set_wells(new_contents, session)  # Use the Plate's set_wells logic

            # Make sure to update the Collection's quantity as well
            session.commit()

    def get_well_quantity(self, plate: Plate, well_id: str) -> Optional[float]:
        """
        Retrieve the quantity in a specific well of a plate resource.

        Args:
            plate (Plate): The plate resource to query.
            well_id (str): The ID of the well to retrieve the quantity for.

        Returns:
            Optional[float]: The quantity in the well, or None if the well does not exist.
        """
        with self.session as session:
            plate = session.merge(plate)
            wells = plate.get_wells(session)
            well = wells.get(well_id)

            if well is not None:
                return well.quantity
            else:
                print(f"Well {well_id} not found in plate {plate.name}")
                return None

    def increase_well(self, plate: Plate, well_id: str, quantity: float) -> None:
        """
        Increase the quantity of liquid in a specific well of a plate.

        Args:
            plate (Plate): The plate resource to update.
            well_id (str): The well ID to increase the quantity for.
            quantity (float): The amount to increase the well quantity by.
        """
        with self.session as session:
            # Find the corresponding collection (plate)
            collection = session.query(Collection).filter_by(name=plate.name).first()

            if not collection:
                raise ValueError(f"Collection for plate {plate.name} not found.")

            plate.increase_well(well_id, quantity, session)
            session.commit()
            session.refresh(collection)  # Refresh the collection object if needed

    def decrease_well(self, plate: Plate, well_id: str, quantity: float) -> None:
        """
        Decrease the quantity of liquid in a specific well of a plate.

        Args:
            plate (Plate): The plate resource to update.
            well_id (str): The well ID to decrease the quantity for.
            quantity (float): The amount to decrease the well quantity by.
        """
        with self.session as session:
            # Find the corresponding collection (plate) in the database
            collection = session.query(Collection).filter_by(name=plate.name).first()

            if not collection:
                raise ValueError(f"Collection for plate {plate.name} not found.")

            plate.decrease_well(well_id, quantity, session)
            session.commit()
            session.refresh(collection)

    def get_wells(self, plate: Plate) -> Dict[str, Pool]:
        """
        Retrieve the entire contents (wells) of a plate resource.

        Args:
            plate (Plate): The plate resource to query.

        Returns:
            Dict[str, Pool]: A dictionary of all wells in the plate, keyed by their well IDs.
        """
        with self.session as session:
            wells = plate.get_wells(session)
            return wells


if __name__ == "__main__":
    resource_interface = ResourcesInterface()
    print(resource_interface.get_all_resources(Asset))
    print(resource_interface.get_resource("Test Stack", "test2"))
    resource_interface.clear_all_table_records()
    pool = Pool(
        name="Test Pool",
        description="A test pool",
        capacity=100.0,
        quantity=50.0,
        owner_name="test1",
    )
    pool = resource_interface.add_resource(pool)
    all_pools = resource_interface.get_all_resources(Pool)
    print("\nAll Pools after modification:", all_pools)
    resource_interface.increase_pool_quantity(pool, 0.0)
    all_pools = resource_interface.get_all_resources(Pool)
    print("\nAll Pools after modification:", all_pools)
    stack = Stack(
        name="Test Stack", description="A test stack", capacity=10, owner_name="test2"
    )
    stack = resource_interface.add_resource(stack)
    retrieved_stack = resource_interface.get_resource(
        resource_name="Test Stack", owner_name="test2"
    )
    print("Retreived_STACK:", retrieved_stack)
    asset = Asset(name="Test Asset", unique_resource=False)
    asset3 = Asset(name="Test Asset3", unique_resource=False)
    resource_interface.push_to_stack(stack, asset)
    resource_interface.push_to_stack(stack, asset3)
    all_stacks = resource_interface.get_all_resources(Stack)
    print("\nAll Stacks after modification:", all_stacks)
    popped_asset = resource_interface.pop_from_stack(stack)
    all_stacks = resource_interface.get_all_resources(Stack)
    print("\nAll Stacks after modification:", all_stacks)
    queue = Queue(
        name="Test Queue", description="A test queue", capacity=10, owner_name="test3"
    )
    queue = resource_interface.add_resource(queue)
    asset2 = Asset(name="Test Asset2")
    resource_interface.push_to_queue(queue, asset2)
    # resource_interface.push_to_queue(queue, asset)
    all_queues = resource_interface.get_all_resources(Queue)
    print("\nAll Queues after modification:", all_queues)
    popped_asset_q = resource_interface.pop_from_queue(queue)
    print("\nPopped Asset from Queue:", popped_asset_q)
    all_queues = resource_interface.get_all_resources(Queue)
    print("\nAll Queues after modification:", all_queues)
    collection = Collection(
        name="Test Collection",
        description="A test collection",
        capacity=10,
        owner_name="test4",
    )
    collection = resource_interface.add_resource(collection)
    resource_interface.insert_into_collection(collection, location="1", asset=asset3)
    retrieved_asset = resource_interface.retrieve_from_collection(
        collection, location=1
    )
    print("\nRetrieved Asset from Collection:", retrieved_asset)
    plate = Plate(
        name="Test Plate",
        description="A test plate",
        capacity=96,
        well_capacity=100.0,
        owner_name="test5",
        unique_resource=False,
    )
    plate2 = Plate(
        name="Test Plate",
        description="A test plate",
        capacity=96,
        well_capacity=100.0,
        owner_name="test5",
        unique_resource=False,
    )
    plate = resource_interface.add_resource(plate)
    plate2 = resource_interface.add_resource(plate2)
    wells_to_add = {
        "A1": 50.0,
        "B1": 66.0,
    }
    resource_interface.update_plate_contents(plate, wells_to_add)
    all_wells = resource_interface.get_wells(plate)
    print(f"All wells in the plate: {all_wells}")
    resource_interface.increase_well(plate, well_id="A1", quantity=20.0)
    resource_interface.decrease_well(plate, well_id="B1", quantity=10.0)
    new_well_to_add = {
        "C1": 70.0,
    }
    resource_interface.update_plate_contents(plate, new_well_to_add)
    updated_wells = resource_interface.get_wells(plate)
    print(f"Updated wells: {updated_wells}")
    resource_interface.update_plate_well(plate, well_id="A1", quantity=80.0)
    all_plates = resource_interface.get_all_resources(Plate)
    print("\nAll Plates after modification:", all_plates)
    new_well_to_add2 = {
        "D1": 70.0,  # Well C1 with 70.0 quantity
    }

    r = resource_interface.get_resource(resource_id=plate2.id)
    resource_interface.update_plate_contents(r, new_well_to_add2)

    # all_asset = resource_interface.get_all_resources(Asset)
    # print("\n Asset Table", all_asset)

    # print(resource_interface.get_resource_type(stack.id))

    # print(resource_interface.get_all_assets_with_relations())
