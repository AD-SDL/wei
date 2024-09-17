"""Types related to the Workcell"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import Field, field_validator

from wei.types.base_types import BaseModel, Metadata, PathLike
from wei.types.module_types import ModuleDefinition


class Workcell(BaseModel):
    """Container for definition of a workcell, as used in a workcell file"""

    name: str
    """Name of the workflow"""
    metadata: Metadata = Field(default_factory=Metadata)
    """Information about the workcell"""
    config: "WorkcellConfig"
    """Globus search index, needed for publishing"""
    modules: List[ModuleDefinition]
    """The modules available to a workcell"""
    locations: Dict[str, Any] = {}
    """Locations used by the workcell"""


class Location(BaseModel):
    """Container for a location"""

    name: str
    """Name of the location"""
    coordinates: Dict[str, Any]
    """Coordinates of the location"""
    state: str = "Empty"
    """State of the location"""
    reserved: Optional[str] = None
    """ID of WorkflowRun that will next occupy this Location"""


class WorkcellConfig(BaseModel, extra="allow"):
    """Defines the format for a workcell config
    Note: the extra='allow' parameter allows for
    extra fields to be added to the config, beyond what's defined below
    """

    lab_name: str = Field(
        default="sdl",
        description="Name of the lab to associate the workcell and all associated data with",
    )
    use_diaspora: bool = Field(
        default=False, description="Whether or not to use diaspora"
    )
    kafka_topic: str = Field(
        default="wei_diaspora",
        description="The Kafka topic to publish to if using diaspora",
    )
    verify_locations_before_transfer: bool = Field(
        default=False,
        description="Whether or not to verify locations are empty before transfer",
    )
    sequential_scheduler: bool = Field(
        default=True,
        description="Whether or not to schedule workflows sequentially or concurrently",
    )
    reset_locations: bool = Field(
        default=True,
        description="Whether or not to reset locations when the Engine (re)starts",
    )
    clear_workflow_runs: bool = Field(
        default=False,
        description="Whether or not to clear workflow runs when the Engine (re)starts",
    )
    update_interval: float = Field(
        default=5.0, description="How often to update the workcell state"
    )
    server_host: str = Field(
        default="0.0.0.0", description="Hostname for the WEI server"
    )
    server_port: int = Field(default=8000, description="Port for the WEI server")
    redis_host: str = Field(
        default="localhost", description="Hostname for the Redis server"
    )
    redis_port: int = Field(default=6379, description="Port for the Redis server")
    redis_password: str = Field(
        default="", description="Password for the Redis server, if any"
    )
    data_directory: PathLike = Field(
        default=Path.home() / ".wei",
        description="Directory to store data produced by WEI",
    )
    log_level: int = Field(default=logging.INFO, description="Logging level for WEI")
    cold_start_delay: int = Field(
        default=2, description="Delay before starting the engine"
    )
    smtp_server: str = Field(
        default="mailgateway.anl.gov", description="Hostname for the SMTP server"
    )
    smtp_port: int = Field(default=25, description="Port number for the SMTP server")
    autostart_engine: bool = Field(
        default=True,
        description="Whether or not to start the engine and scheduler for the workcell from the server process (set to False if you want/need to run the engine as a separate process/container). This will default to True in the future.",
    )

    # Validators
    @field_validator("data_directory")
    @classmethod
    def validate_data_directory(cls, v: PathLike) -> Path:
        """Converts the data_directory to a Path object"""
        return Path(v)
