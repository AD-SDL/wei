"""Resources interface"""

import json
from typing import Any, Dict, List, Optional, Type

from pydantic import BaseModel
from sqlmodel import Field, Session, SQLModel, create_engine, select

from wei.types.resource_types import Asset, Collection, Plate, Pool, StackResource


class Resource(SQLModel, table=True):
    """
    Database model representing a resource entry.

    Attributes:
        id (Optional[int]): The primary key of the resource entry.
        resource_id (str): The unique identifier for the resource.
        name (Optional[str]): The name of the resource.
        resource_data (str): JSON string representing the resource data.
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    resource_id: str
    name: Optional[str]
    resource_data: str


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

    def add_resource(self, resource: BaseModel, name: Optional[str] = None) -> Resource:
        """
        Add a new resource to the database.

        Args:
            resource (BaseModel): The resource to add.
            name (Optional[str]): The name of the resource.

        Returns:
            Resource: The added resource with updated state.
        """
        resource_data = resource.json()
        resource_entry = Resource(
            resource_id=resource.id, name=name, resource_data=resource_data
        )

        with self.get_session() as session:
            session.add(resource_entry)
            session.commit()
            session.refresh(resource_entry)
        return resource_entry

    def get_all_resources(self) -> List[Resource]:
        """
        Retrieve all resources from the database.

        Returns:
            List[Resource]: List of all resources.
        """
        with self.get_session() as session:
            resources = session.exec(select(Resource)).all()
        return resources

    def get_resource(self, resource_id: str) -> Optional[Resource]:
        """
        Retrieve a resource by its ID.

        Args:
            resource_id (str): The ID of the resource.

        Returns:
            Resource: The retrieved resource, or None if not found.
        """
        with self.get_session() as session:
            resource = session.exec(
                select(Resource).where(Resource.resource_id == resource_id)
            ).one_or_none()
        return resource

    def update_resource(
        self, resource_id: str, updates: Dict[str, Any]
    ) -> Optional[Resource]:
        """
        Update a resource with new data.

        Args:
            resource_id (str): The ID of the resource to update.
            updates (dict): A dictionary of updates to apply.

        Returns:
            Resource: The updated resource, or None if not found.
        """
        with self.get_session() as session:
            resource = session.exec(
                select(Resource).where(Resource.resource_id == resource_id)
            ).one_or_none()
            if resource:
                resource_data = json.loads(resource.resource_data)
                resource_data.update(updates)
                resource.resource_data = json.dumps(resource_data)
                session.add(resource)
                session.commit()
                session.refresh(resource)
        return resource

    def delete_resource(self, resource_id: str) -> Optional[Resource]:
        """
        Delete a resource from the database.

        Args:
            resource_id (str): The ID of the resource to delete.

        Returns:
            Resource: The deleted resource, or None if not found.
        """
        with self.get_session() as session:
            resource = session.exec(
                select(Resource).where(Resource.resource_id == resource_id)
            ).one_or_none()
            if resource:
                session.delete(resource)
                session.commit()
        return resource

    def deserialize_resource(
        self, resource: Resource, resource_type: Type[BaseModel]
    ) -> BaseModel:
        """
        Deserialize a resource from the database.

        Args:
            resource (Resource): The resource entry from the database.
            resource_type (Type[BaseModel]): The Pydantic model type to deserialize to.

        Returns:
            BaseModel: The deserialized resource.
        """
        resource_data = json.loads(resource.resource_data)
        return resource_type.parse_obj(resource_data)

    def push_asset(self, resource_id: str, asset: Asset) -> Optional[Resource]:
        """
        Push an asset to a stack or queue resource.

        Args:
            resource_id (str): The ID of the resource.
            asset (Asset): The asset to push.

        Returns:
            Resource: The updated resource, or None if not found.
        """
        resource = self.get_resource(resource_id)
        if not resource:
            return None
        resource_obj = self.deserialize_resource(resource, StackResource)
        resource_obj.push(asset)
        return self.update_resource(
            resource_id, {"contents": [item.dict() for item in resource_obj.contents]}
        )

    def pop_asset(self, resource_id: str) -> Optional[Asset]:
        """
        Pop an asset from a stack or queue resource.

        Args:
            resource_id (str): The ID of the resource.

        Returns:
            Asset: The popped asset, or None if the resource is not found or empty.
        """
        resource = self.get_resource(resource_id)
        if not resource:
            return None
        resource_obj = self.deserialize_resource(resource, StackResource)
        asset = resource_obj.pop()
        self.update_resource(
            resource_id, {"contents": [item.dict() for item in resource_obj.contents]}
        )
        return asset

    def increase_quantity(self, resource_id: str, amount: float) -> Optional[Resource]:
        """
        Increase the quantity of a pool resource.

        Args:
            resource_id (str): The ID of the resource.
            amount (float): The amount to increase.

        Returns:
            Resource: The updated resource, or None if not found.
        """
        resource = self.get_resource(resource_id)
        if not resource:
            return None
        resource_obj = self.deserialize_resource(resource, Pool)
        resource_obj.increase(amount)
        updated_resource = self.update_resource(
            resource_id, {"quantity": resource_obj.quantity}
        )
        return updated_resource

    def decrease_quantity(self, resource_id: str, amount: float) -> Optional[Resource]:
        """
        Decrease the quantity of a pool resource.

        Args:
            resource_id (str): The ID of the resource.
            amount (float): The amount to decrease.

        Returns:
            Resource: The updated resource, or None if not found.
        """
        resource = self.get_resource(resource_id)
        if not resource:
            return None
        resource_obj = self.deserialize_resource(resource, Pool)
        resource_obj.decrease(amount)
        updated_resource = self.update_resource(
            resource_id, {"quantity": resource_obj.quantity}
        )
        return updated_resource

    def insert_asset(
        self, resource_id: str, location: str, asset: Asset
    ) -> Optional[Resource]:
        """
        Insert an asset into a collection resource at a specific location.

        Args:
            resource_id (str): The ID of the collection resource.
            location (str): The location to insert the asset.
            asset (Asset): The asset to insert.

        Returns:
            Resource: The updated collection resource, or None if not found.
        """
        resource = self.get_resource(resource_id)
        if not resource:
            return None
        resource_obj = self.deserialize_resource(resource, Collection)
        resource_obj.insert(location, asset)
        return self.update_resource(
            resource_id,
            {"contents": {k: v.dict() for k, v in resource_obj.contents.items()}},
        )

    def retrieve_asset(self, resource_id: str, location: str) -> Optional[Asset]:
        """
        Retrieve an asset from a collection resource at a specific location.

        Args:
            resource_id (str): The ID of the collection resource.
            location (str): The location of the asset to retrieve.

        Returns:
            Asset: The retrieved asset, or None if not found.
        """
        resource = self.get_resource(resource_id)
        if not resource:
            return None
        resource_obj = self.deserialize_resource(resource, Collection)
        asset = resource_obj.retrieve(location)
        self.update_resource(
            resource_id,
            {"contents": {k: v.dict() for k, v in resource_obj.contents.items()}},
        )
        return asset

    def update_plate(
        self, resource_id: str, new_contents: Dict[str, float]
    ) -> Optional[Resource]:
        """
        Update the contents of a plate resource.

        Args:
            resource_id (str): The ID of the plate resource.
            new_contents (Dict[str, float]): The new contents to update.

        Returns:
            Resource: The updated plate resource, or None if not found.
        """
        resource = self.get_resource(resource_id)
        if not resource:
            return None
        resource_obj = self.deserialize_resource(resource, Plate)
        resource_obj.update_plate(new_contents)
        return self.update_resource(
            resource_id,
            {
                "contents": {k: v.dict() for k, v in resource_obj.wells.items()},
                "wells": {k: v.dict() for k, v in resource_obj.wells.items()},
            },
        )

    def update_plate_well(
        self, resource_id: str, well_id: str, quantity: float
    ) -> Optional[Resource]:
        """
        Update the quantity of a specific well in a plate resource.

        Args:
            resource_id (str): The ID of the plate resource.
            well_id (str): The ID of the well to update.
            quantity (float): The new quantity for the well.

        Returns:
            Resource: The updated plate resource, or None if not found.
        """
        resource = self.get_resource(resource_id)
        if not resource:
            return None
        resource_obj = self.deserialize_resource(resource, Plate)
        if well_id in resource_obj.wells:
            resource_obj.wells[well_id].quantity = quantity
        else:
            resource_obj.wells[well_id] = Pool(
                description=f"Well {well_id}",
                name=f"Well{well_id}",
                capacity=resource_obj.well_capacity,
                quantity=quantity,
            )
        return self.update_resource(
            resource_id,
            {"contents": {k: v.dict() for k, v in resource_obj.wells.items()}},
        )


# Example Usage of ResourceInterface
if __name__ == "__main__":
    from wei.types.resource_types import Asset, Collection, Plate, Pool, StackResource

    resource_interface = ResourceInterface(database_url="sqlite:///:memory:")

    # Example 1: Add a Pool Resource
    pool_resource = Pool(
        description="Test Pool", name="TestPool", capacity=100.0, quantity=50.0
    )
    created_pool = resource_interface.add_resource(
        pool_resource, name="Test Pool Resource"
    )
    # print("\n Added Pool Resource:", created_pool)

    # Example 2: Add a StackResource
    stack_resource = StackResource(
        description="Test Stack", name="TestStack", capacity=10
    )
    stack_resource.push(Asset(name="TestAsset1"))
    created_stack = resource_interface.add_resource(
        stack_resource, name="Test Stack Resource"
    )
    # print("\n Added Stack Resource:", created_stack)

    # Example 3: Add a Plate Resource
    plate_resource = Plate(name="TestPlate", well_capacity=100.0)
    plate_resource.update_plate({f"A{col}": 50.0 for col in range(1, 3)})
    created_plate = resource_interface.add_resource(
        plate_resource, name="Test Plate Resource"
    )
    # print("\n Added Plate Resource:", created_plate)

    # Example 4: Retrieve All Resources
    all_resources = resource_interface.get_all_resources()
    print("\n All Resources:", all_resources)

    # Example 5: Get a Specific Resource by ID
    resource_id = created_pool.resource_id
    retrieved_pool = resource_interface.get_resource(resource_id)
    print("\n Retrieved Pool Resource by ID:", retrieved_pool)

    # Example 6: Update a Resource
    updated_pool = resource_interface.update_resource(resource_id, {"quantity": 60.0})
    print("\n Updated Pool Resource:", updated_pool)

    # Example 7: Delete a Resource
    # deleted_resource = resource_interface.delete_resource(resource_id)
    # print("\n Deleted Resource:", deleted_resource)

    # # Example 8: Deserialize a Resource
    # deserialized_pool = resource_interface.deserialize_resource(created_pool, Pool)
    # print("\n Deserialized Pool Resource:", deserialized_pool)

    # Example 9: Push an Asset to StackResource
    # resource_interface.push_asset(created_stack.resource_id, Asset(name="TestAsset2"))
    # updated_stack = resource_interface.get_resource(created_stack.resource_id)
    # print("\n Updated Stack after push:", updated_stack)

    # Example 10: Pop an Asset from StackResource
    # popped_asset = resource_interface.pop_asset(created_stack.resource_id)
    # print("\n Popped Asset from Stack:", popped_asset)

    # Example 11: Increase Pool Quantity
    resource_interface.increase_quantity(created_pool.resource_id, 20.0)
    updated_pool = resource_interface.get_resource(created_pool.resource_id)
    print("\n Increased Pool Quantity:", updated_pool)

    # Example 12: Decrease Pool Quantity
    resource_interface.decrease_quantity(created_pool.resource_id, 10.0)
    updated_pool = resource_interface.get_resource(created_pool.resource_id)
    print("\n Decreased Pool Quantity:", updated_pool)

    # Example 13: Insert an Asset into Collection
    collection_resource = Collection(
        description="Test Collection", name="TestCollection", capacity=5
    )
    created_collection = resource_interface.add_resource(
        collection_resource, name="Test Collection Resource"
    )
    resource_interface.insert_asset(
        created_collection.resource_id, "location1", Asset(name="TestAsset1")
    )
    updated_collection = resource_interface.get_resource(created_collection.resource_id)
    print("\n Updated Collection after insert:", updated_collection)

    # Example 14: Retrieve an Asset from Collection
    retrieved_asset = resource_interface.retrieve_asset(
        created_collection.resource_id, "location1"
    )
    print("\n Retrieved Asset from Collection:", retrieved_asset)

    # Example 15: Update Plate Contents
    resource_interface.update_plate(
        created_plate.resource_id, {f"A{col}": 75.0 for col in range(1, 5)}
    )
    updated_plate = resource_interface.get_resource(created_plate.resource_id)
    print("\n Updated Plate Contents:", updated_plate)

    # Example 16: Update Specific Well in Plate
    # resource_interface.update_plate_well(created_plate.resource_id, "A1", 80.0)
    # updated_plate = resource_interface.get_resource(created_plate.resource_id)
    # print("\n Updated Specific Well in Plate:", updated_plate)
