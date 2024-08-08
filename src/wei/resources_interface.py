"""Resources Interface"""

from typing import Dict, List, Optional, Type

from sqlmodel import Session, SQLModel, create_engine, select

from wei.types.resource_types import AssetTable, Collection, Plate, Pool, Queue, Stack


class ResourceInterface:
    """Interface to work with resources database"""

    def __init__(self, database_url: Optional[str] = None):
        """
        Initialize the ResourceInterface with a SQLAlchemy engine.

        Args:
            database_url (str): The URL for the database connection.
        """
        if database_url is None:
            database_url = "sqlite:///database.db"
        self.engine = create_engine(database_url)
        SQLModel.metadata.create_all(self.engine)

    def get_session(self) -> Session:
        """
        Create a new SQLAlchemy session.

        Returns:
            Session: A new SQLAlchemy session.
        """
        return Session(self.engine)

    def get_all_resources(self, resource_type: Type[SQLModel]) -> List[SQLModel]:
        """
        Retrieve all resources from the database.

        Args:
            resource_type (Type[SQLModel]): The type of the resource to retrieve.

        Returns:
            List[SQLModel]: List of all resources of the specified type.
        """
        with self.get_session() as session:
            statement = select(resource_type)
            resources = session.exec(statement).all()
        return resources

    def add_resource(self, resource: SQLModel) -> SQLModel:
        """
        Add a new resource to the database.

        Args:
            resource (SQLModel): The resource to add.

        Returns:
            SQLModel: The added resource with updated state.
        """
        with self.get_session() as session:
            session.add(resource)
            session.commit()
            session.refresh(resource)
        return resource

    def get_resource(
        self, resource_type: Type[SQLModel], resource_id: str
    ) -> Optional[SQLModel]:
        """
        Retrieve a resource by its ID.

        Args:
            resource_type (Type[SQLModel]): The type of the resource.
            resource_id (str): The ID of the resource to retrieve.

        Returns:
            SQLModel: The retrieved resource, or None if not found.
        """
        with self.get_session() as session:
            statement = select(resource_type).where(resource_type.id == resource_id)
            resource = session.exec(statement).one_or_none()
        return resource

    def update_resource(
        self, resource_type: Type[SQLModel], resource_id: str, updates: Dict[str, any]
    ) -> Optional[SQLModel]:
        """
        Update a resource with new data.

        Args:
            resource_type (Type[SQLModel]): The type of the resource.
            resource_id (str): The ID of the resource to update.
            updates (dict): A dictionary of updates to apply.

        Returns:
            SQLModel: The updated resource, or None if not found.
        """
        with self.get_session() as session:
            resource = self.get_resource(resource_type, resource_id)
            if resource:
                for key, value in updates.items():
                    setattr(resource, key, value)
                session.add(resource)
                session.commit()
                session.refresh(resource)
        return resource

    def delete_resource(
        self, resource_type: Type[SQLModel], resource_id: str
    ) -> Optional[SQLModel]:
        """
        Delete a resource from the database.

        Args:
            resource_type (Type[SQLModel]): The type of the resource.
            resource_id (str): The ID of the resource to delete.

        Returns:
            SQLModel: The deleted resource, or None if not found.
        """
        with self.get_session() as session:
            resource = self.get_resource(resource_type, resource_id)
            if resource:
                session.delete(resource)
                session.commit()
        return resource

    def push_asset(
        self, resource_id: str, asset_id: str, resource_type: Type[SQLModel]
    ) -> Optional[SQLModel]:
        """
        Push an asset to a stack or queue resource.

        Args:
            resource_id (str): The ID of the resource.
            asset_id (str): The ID of the asset to push.
            resource_type (Type[SQLModel]): The type of the resource.

        Returns:
            SQLModel: The updated resource, or None if not found.
        """
        resource = self.get_resource(resource_type, resource_id)
        if resource and isinstance(resource, Stack):
            resource.push(asset_id)
            self.update_resource(
                resource_type, resource_id, {"contents": resource.contents}
            )
            return resource
        return None

    def pop_asset(
        self, resource_id: str, resource_type: Type[SQLModel]
    ) -> Optional[str]:
        """
        Pop an asset from a stack or queue resource.

        Args:
            resource_id (str): The ID of the resource.
            resource_type (Type[SQLModel]): The type of the resource.

        Returns:
            str: The ID of the popped asset, or None if not found.
        """
        with self.get_session() as session:  # Noqa
            resource = self.get_resource(resource_type, resource_id)
            if resource and isinstance(resource, (Stack, Queue)):
                asset_id = resource.pop()
                self.update_resource(
                    resource_type, resource_id, {"contents": resource.contents}
                )
                return asset_id
        return None

    def increase_quantity(
        self, resource_id: str, amount: float, resource_type: Type[SQLModel]
    ) -> Optional[SQLModel]:
        """
        Increase the quantity of a pool resource.

        Args:
            resource_id (str): The ID of the resource.
            amount (float): The amount to increase.
            resource_type (Type[SQLModel]): The type of the resource.

        Returns:
            SQLModel: The updated resource, or None if not found.
        """
        resource = self.get_resource(resource_type, resource_id)
        if not resource:
            return None

        if isinstance(resource, Pool):
            resource.increase(amount)
            self.update_resource(
                resource_type, resource_id, {"quantity": resource.quantity}
            )
            return resource
        return None

    def decrease_quantity(
        self, resource_id: str, amount: float, resource_type: Type[SQLModel]
    ) -> Optional[SQLModel]:
        """
        Decrease the quantity of a pool resource.

        Args:
            resource_id (str): The ID of the resource.
            amount (float): The amount to decrease.
            resource_type (Type[SQLModel]): The type of the resource.

        Returns:
            SQLModel: The updated resource, or None if not found.
        """
        resource = self.get_resource(resource_type, resource_id)
        if not resource:
            return None

        if isinstance(resource, Pool):
            resource.decrease(amount)
            self.update_resource(
                resource_type, resource_id, {"quantity": resource.quantity}
            )
            return resource
        return None

    def insert_asset(
        self,
        resource_id: str,
        location: str,
        asset_id: str,
        resource_type: Type[SQLModel],
    ) -> Optional[SQLModel]:
        """
        Insert an asset into a collection resource at a specific location.

        Args:
            resource_id (str): The ID of the collection resource.
            location (str): The location to insert the asset.
            asset_id (str): The ID of the asset to insert.
            resource_type (Type[SQLModel]): The type of the resource.

        Returns:
            SQLModel: The updated collection resource, or None if not found.
        """
        resource = self.get_resource(resource_type, resource_id)
        if not resource:
            return None

        if isinstance(resource, Collection):
            resource.insert(location, asset_id)
            self.update_resource(
                resource_type, resource_id, {"contents": resource.contents}
            )
            return resource
        return None

    def retrieve_asset(
        self, resource_id: str, location: str, resource_type: Type[SQLModel]
    ) -> Optional[str]:
        """
        Retrieve an asset from a collection resource at a specific location.

        Args:
            resource_id (str): The ID of the collection resource.
            location (str): The location of the asset to retrieve.
            resource_type (Type[SQLModel]): The type of the resource.

        Returns:
            str: The retrieved asset ID, or None if not found.
        """
        resource = self.get_resource(resource_type, resource_id)
        if not resource:
            return None

        if isinstance(resource, Collection):
            asset_id = resource.retrieve(location)
            self.update_resource(
                resource_type, resource_id, {"contents": resource.contents}
            )
            return asset_id
        return None

    def update_plate(
        self,
        resource_id: str,
        new_contents: Dict[str, float],
        resource_type: Type[SQLModel],
    ) -> Optional[SQLModel]:
        """
        Update the contents of a plate resource.

        Args:
            resource_id (str): The ID of the plate resource.
            new_contents (Dict[str, float]): The new contents to update.
            resource_type (Type[SQLModel]): The type of the resource.

        Returns:
            SQLModel: The updated plate resource, or None if not found.
        """
        resource = self.get_resource(resource_type, resource_id)
        if not resource:
            return None

        if isinstance(resource, Plate):
            resource.update_plate(new_contents)
            self.update_resource(
                resource_type, resource_id, {"contents": resource.contents}
            )
            return resource
        return None

    def update_plate_well(
        self,
        resource_id: str,
        well_id: str,
        quantity: float,
        resource_type: Type[SQLModel],
    ) -> Optional[SQLModel]:
        """
        Update the quantity of a specific well in a plate resource.

        Args:
            resource_id (str): The ID of the plate resource.
            well_id (str): The ID of the well to update.
            quantity (float): The new quantity for the well.
            resource_type (Type[SQLModel]): The type of the resource.

        Returns:
            SQLModel: The updated plate resource, or None if not found.
        """
        resource = self.get_resource(resource_type, resource_id)
        if not resource:
            return None

        if isinstance(resource, Plate):
            contents_dict = resource.contents  # Directly use the dictionary
            if well_id in contents_dict:
                pool_id = contents_dict[well_id]
                pool = self.get_resource(Pool, pool_id)
                if pool:
                    pool.quantity = quantity
                    self.update_resource(Pool, pool_id, {"quantity": quantity})
            else:
                pool = Pool(
                    description=f"Well {well_id}",
                    name=f"Well{well_id}",
                    capacity=resource.well_capacity,
                    quantity=quantity,
                )
                created_pool = self.add_resource(pool)
                contents_dict[well_id] = created_pool.id
            resource.contents = contents_dict  # Assign back the updated dictionary
            self.update_resource(
                resource_type, resource_id, {"contents": resource.contents}
            )
            return resource
        return None


if __name__ == "__main__":
    resource_interface = ResourceInterface(database_url="sqlite:///:memory:")

    # # Example usage: Create a Pool resource
    # pool = Pool(name="Test Pool", description="A test pool", capacity=100.0, quantity=50.0)
    # created_pool = resource_interface.add_resource(pool)
    # print("Created Pool:", created_pool)

    # # Example usage: Increase quantity in the Pool
    # updated_pool = resource_interface.increase_quantity(created_pool.id, 25.0, Pool)
    # print("Increased Pool Quantity:", updated_pool)

    # # Example usage: Create a Stack resource
    # stack = Stack(name="Test Stack", description="A test stack", capacity=10)
    # created_stack = resource_interface.add_resource(stack)
    # print("Created Stack:", created_stack)

    # # Example usage: Push an asset to the Stack
    # asset = AssetTable(name="Test Asset")
    # created_asset = resource_interface.add_resource(asset)
    # updated_stack = resource_interface.push_asset(created_stack.id, created_asset.id, Stack)
    # print("Updated Stack with Pushed Asset:", updated_stack)

    # # Example usage: Pop an asset from the Stack
    # popped_asset_id = resource_interface.pop_asset(created_stack.id, Stack)
    # print("Popped Asset ID from Stack:", popped_asset_id)

    # # Example usage: Create a Queue resource
    # queue = Queue(name="Test Queue", description="A test queue", capacity=10)
    # created_queue = resource_interface.add_resource(queue)
    # print("Created Queue:", created_queue)

    # # Example usage: Create a Collection resource
    # collection = Collection(name="Test Collection", description="A test collection", capacity=10)
    # created_collection = resource_interface.add_resource(collection)
    # print("Created Collection:", created_collection)

    # # Example usage: Insert an asset into the Collection
    # resource_interface.insert_asset(created_collection.id, "location1", created_asset.id, Collection)
    # updated_collection = resource_interface.get_resource(Collection, created_collection.id)
    # print("Updated Collection with Inserted Asset:", updated_collection)

    # # Example usage: Retrieve an asset from the Collection
    # retrieved_asset_id = resource_interface.retrieve_asset(created_collection.id, "location1", Collection)
    # print("Retrieved Asset ID from Collection:", retrieved_asset_id)

    # # Example usage: Create a Plate resource
    # plate = Plate(name="Test Plate", description="A test plate", well_capacity=100.0)
    # created_plate = resource_interface.add_resource(plate)
    # print("Created Plate:", created_plate)

    # # Example usage: Update the contents of the Plate
    # resource_interface.update_plate(created_plate.id, {"A1": 75.0, "A2": 75.0, "A3": 75.0, "A4": 75.0}, Plate)
    # updated_plate = resource_interface.get_resource(Plate, created_plate.id)
    # print("Updated Plate Contents:", updated_plate)

    # # Example usage: Update a specific well in the Plate
    # resource_interface.update_plate_well(created_plate.id, "A1", 80.0, Plate)
    # updated_plate = resource_interface.get_resource(Plate, created_plate.id)
    # print("Updated Specific Well in Plate:", updated_plate)

    # # Example usage: Get all resources of a specific type
    # all_stacks = resource_interface.get_all_resources(Stack)
    # print("All Stacks:", all_stacks)
    # Add resources

    # Add resources
    stack1 = Stack(
        description="Stack for transfer",
        name="Stack1",
        capacity=10,
    )
    created_stack1 = resource_interface.add_resource(stack1)

    for asset_name in ["Plate1", "Plate2", "Plate3"]:
        asset = AssetTable(name=asset_name, stack_resource_id=created_stack1.id)
        created_asset = resource_interface.add_resource(asset)
        resource_interface.push_asset(created_stack1.id, created_asset.id, Stack)

    stack2 = Stack(
        description="Stack for transfer",
        name="Stack2",
        capacity=10,
    )
    resource_interface.add_resource(stack2)

    stack3 = Stack(
        description="Stack for transfer",
        name="Stack3",
        capacity=1,
    )
    resource_interface.add_resource(stack3)

    trash_stack = Stack(
        description="Trash",
        name="Trash",
        capacity=None,
    )
    resource_interface.add_resource(trash_stack)

    plate_contents = {}
    for row in "ABCDEFGH":
        for col in range(1, 13):
            pool = Pool(
                description=f"Well {row}{col}",
                name=f"Well{row}{col}",
                capacity=100.0,
                quantity=50.0,
            )
            created_pool = resource_interface.add_resource(pool)
            plate_contents[f"{row}{col}"] = created_pool.id

    plate = Plate(
        name="Plate1",
        contents=plate_contents,
        description="A test plate",
        well_capacity=100.0,
    )
    created_plate = resource_interface.add_resource(plate)

    collection = Collection(
        description="Collection for measurement",
        name="CollectionResource",
        capacity=5,
    )
    created_collection = resource_interface.add_resource(collection)
    for i in range(1, 3):
        asset = AssetTable(name=f"Asset{i}", collection_id=created_collection.id)
        created_asset = resource_interface.add_resource(asset)
        resource_interface.insert_asset(
            created_collection.id, str(i), created_asset.id, Collection
        )

    # Example: Retrieve and print all stacks with asset details
    all_stacks = resource_interface.get_all_resources(Stack)
    print(all_stacks)
    for stack in all_stacks:
        asset_details = stack.get_asset_details(resource_interface.get_session())
        print(f"Stack {stack.name} Contents: {asset_details}")

    # # Example: Retrieve and print all plates
    # all_plates = resource_interface.get_all_resources(Plate)
    # print("All Plates:", all_plates)

    # # Example: Retrieve and print all collections
    # all_collections = resource_interface.get_all_resources(Collection)
    # print("All Collections:", all_collections)
