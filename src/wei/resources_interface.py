"""Resources interface"""

from sqlmodel import Session, SQLModel, create_engine, select

from wei.types.resource_types import (
    Collection,
    Pool,
    ResourceContainer,
    StackResource,
)


class ResourceInterface:
    """Interface to work with resources database"""

    def __init__(self, database_url: str = "sqlite:///database.db"):
        """
        Initialize the ResourceInterface with a SQLAlchemy engine.

        Args:
            database_url (str): The URL for the database connection.
        """
        self.engine = create_engine(database_url)
        self.create_db_and_tables()

    def create_db_and_tables(self):
        """
        Create database tables based on the SQLModel definitions.
        """
        SQLModel.metadata.create_all(self.engine)

    def get_session(self):
        """
        Create a new SQLAlchemy session.

        Returns:
            Session: A new SQLAlchemy session.
        """
        return Session(self.engine)

    def get_all_resources(self):
        """
        Retrieve all resources from the database.

        Returns:
            List[ResourceContainer]: List of all resources.
        """
        with self.get_session() as session:
            statement = select(ResourceContainer)
            resources = session.exec(statement).all()
        return resources

    def add_resource(self, resource):
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

    def get_resource(self, resource_id, resource_type):
        """
        Retrieve a resource by its ID.

        Args:
            resource_id (str): The ID of the resource.
            resource_type (SQLModel): The type of the resource.

        Returns:
            SQLModel: The retrieved resource, or None if not found.
        """
        with self.get_session() as session:
            statement = select(resource_type).where(resource_type.id == resource_id)
            result = session.exec(statement).one_or_none()
        return result

    def update_resource(self, resource_id, resource_type, updates):
        """
        Update a resource with new data.

        Args:
            resource_id (str): The ID of the resource to update.
            resource_type (SQLModel): The type of the resource.
            updates (dict): A dictionary of updates to apply.

        Returns:
            SQLModel: The updated resource, or None if not found.
        """
        with self.get_session() as session:
            statement = select(resource_type).where(resource_type.id == resource_id)
            resource = session.exec(statement).one_or_none()
            if resource:
                for key, value in updates.items():
                    setattr(resource, key, value)
                session.add(resource)
                session.commit()
                session.refresh(resource)
        return resource

    def delete_resource(self, resource_id, resource_type):
        """
        Delete a resource from the database.

        Args:
            resource_id (str): The ID of the resource to delete.
            resource_type (SQLModel): The type of the resource.

        Returns:
            SQLModel: The deleted resource, or None if not found.
        """
        with self.get_session() as session:
            statement = select(resource_type).where(resource_type.id == resource_id)
            resource = session.exec(statement).one_or_none()
            if resource:
                session.delete(resource)
                session.commit()
        return resource

    def push_asset(self, resource_id, asset_id):
        """
        Push an asset to a stack resource.

        Args:
            resource_id (str): The ID of the stack resource.
            asset_id (str): The ID of the asset to push.

        Returns:
            SQLModel: The updated stack resource, or None if not found.
        """
        with self.get_session() as session:
            resource = self.get_resource(resource_id, StackResource)
            if resource:
                resource.push(asset_id)
                session.add(resource)
                session.commit()
                session.refresh(resource)
            return resource

    def pop_asset(self, resource_id):
        """
        Pop an asset from a stack resource.

        Args:
            resource_id (str): The ID of the stack resource.

        Returns:
            str: The ID of the popped asset, or None if the resource is not found or empty.
        """
        with self.get_session() as session:
            resource = self.get_resource(resource_id, StackResource)
            if resource:
                asset_id = resource.pop()
                session.add(resource)
                session.commit()
                return asset_id
            return None

    def increase_quantity(self, resource_id, amount):
        """
        Increase the quantity of a pool resource.

        Args:
            resource_id (str): The ID of the pool resource.
            amount (float): The amount to increase.

        Returns:
            SQLModel: The updated pool resource, or None if not found.
        """
        with self.get_session() as session:
            resource = self.get_resource(resource_id, Pool)
            if resource:
                resource.increase(amount)
                session.add(resource)
                session.commit()
                session.refresh(resource)
            return resource

    def decrease_quantity(self, resource_id, amount):
        """
        Decrease the quantity of a pool resource.

        Args:
            resource_id (str): The ID of the pool resource.
            amount (float): The amount to decrease.

        Returns:
            SQLModel: The updated pool resource, or None if not found.
        """
        with self.get_session() as session:
            resource = self.get_resource(resource_id, Pool)
            if resource:
                resource.decrease(amount)
                session.add(resource)
                session.commit()
                session.refresh(resource)
            return resource

    def fill_pool(self, resource_id):
        """
        Fill a pool resource to its capacity.

        Args:
            resource_id (str): The ID of the pool resource.

        Returns:
            SQLModel: The updated pool resource, or None if not found.
        """
        with self.get_session() as session:
            resource = self.get_resource(resource_id, Pool)
            if resource:
                resource.fill()
                session.add(resource)
                session.commit()
                session.refresh(resource)
            return resource

    def empty_pool(self, resource_id):
        """
        Empty a pool resource.

        Args:
            resource_id (str): The ID of the pool resource.

        Returns:
            SQLModel: The updated pool resource, or None if not found.
        """
        with self.get_session() as session:
            resource = self.get_resource(resource_id, Pool)
            if resource:
                resource.empty()
                session.add(resource)
                session.commit()
                session.refresh(resource)
            return resource

    def insert_asset(self, resource_id, location, asset):
        """
        Insert an asset into a collection resource at a specific location.

        Args:
            resource_id (str): The ID of the collection resource.
            location (str): The location to insert the asset.
            asset (Asset): The asset to insert.

        Returns:
            SQLModel: The updated collection resource, or None if not found.
        """
        with self.get_session() as session:
            resource = self.get_resource(resource_id, Collection)
            if resource:
                resource.insert(location, asset)
                session.add(resource)
                session.commit()
                session.refresh(resource)
            return resource

    def retrieve_asset(self, resource_id, location):
        """
        Retrieve an asset from a collection resource at a specific location.

        Args:
            resource_id (str): The ID of the collection resource.
            location (str): The location of the asset to retrieve.

        Returns:
            Asset: The retrieved asset, or None if not found.
        """
        with self.get_session() as session:
            resource = self.get_resource(resource_id, Collection)
            if resource:
                asset = resource.retrieve(location)
                session.add(resource)
                session.commit()
                return asset
            return None
