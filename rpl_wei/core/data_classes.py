"""Dataclasses used for the workflows/cells"""

import json
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, TypeVar, Union
from uuid import UUID, uuid4

import ulid
import yaml
from pydantic import BaseModel as _BaseModel
from pydantic import Field, validator

_T = TypeVar("_T")

PathLike = Union[str, Path]


class BaseModel(_BaseModel):
    """Allows any sub-class to inherit methods allowing for programatic description of protocols
    Can load a yaml into a class and write a class into a yaml file.
    """

    def dict(self, **kwargs):
        """Return the dictionary without the hidden fields

        Returns
        -------
        dict
            Dict representation of the object
        """
        hidden_fields = set(
            attribute_name
            for attribute_name, model_field in self.__fields__.items()
            if model_field.field_info.extra.get("hidden") is True
        )
        kwargs.setdefault("exclude", hidden_fields)
        return super().dict(**kwargs)

    def json(self, **kwargs) -> str:
        """Returns the json representation of the object without the hidden fields

        Returns
        -------
        str
            returns the JSON string of the object
        """
        hidden_fields = set(
            attribute_name
            for attribute_name, model_field in self.__fields__.items()
            if model_field.field_info.extra.get("hidden") is True
        )
        kwargs.setdefault("exclude", hidden_fields)
        return super().json(**kwargs)

    def write_yaml(self, cfg_path: PathLike) -> None:
        """Allows programatic creation of ot2util objects and saving them into yaml.
        Parameters
        ----------
        cfg_path : PathLike
            Path to dump the yaml file.
        Returns
        -------
        None
        """
        with open(cfg_path, mode="w") as fp:
            yaml.dump(json.loads(self.json()), fp, indent=4, sort_keys=False)

    @classmethod
    def from_yaml(cls: Type[_T], filename: PathLike) -> _T:
        """Allows loading of yaml into ot2util objects.
        Parameters
        ----------
        filename: PathLike
            Path to yaml file location.
        """
        with open(filename) as fp:
            raw_data = yaml.safe_load(fp)
        return cls(**raw_data)  # type: ignore[call-arg]


class Tag(BaseModel):
    """Vision tag"""

    type: str
    """Type of the tag"""
    id: str  # not quite sure what this will be
    """Id of the tag """


class Module(BaseModel):
    """Container for a module found in a workcell file (more info than in a workflow file)"""

    # Hidden
    config_validation: Optional[Path] = Field(
        Path(__file__).parent.resolve() / "data/module_configs_validation.json",
        hidden=True,
    )

    # Public
    name: str
    """name of the module, should be opentrons api compatible"""
    model: Optional[str]
    """type of the robot (e.g OT2, pf400, etc.) """
    interface: str
    """Type of client (e.g ros_wei_client)"""
    config: Dict
    """the necessary configuration for the robot, arbitrary dict"""
    positions: Optional[dict]
    """Optional, if the robot supports positions we will use them"""
    tag: Optional[Tag]
    """Vision tag"""
    id: UUID = Field(default_factory=uuid4)
    """Robot id"""

    # TODO: Think about new validators based on backend types, e.g rosnodes, docker containers
    @validator("config")
    def validate_config(cls, v, values, **kwargs):
        """Validate the config field of the workcell config with special rules for each type of robot"""
        config_validation = json.load(values["config_validation"].open())
        interface_type = values.get("interface", "").lower()

        if interface_type.lower() not in config_validation:
            raise ValueError(
                f"Module type {interface_type} not in configuration validators"
            )

        req_fields = config_validation[interface_type]
        for field in req_fields:
            if field not in v:
                raise ValueError(f"Required field `{field}` not in values")

        return v


class SimpleModule(BaseModel):
    """Simple module for use in the workflow file (does not need as much info)"""

    name: str
    """Name, should correspond with a module rosnode"""


class Interface(BaseModel):
    """standardizes communications with different damons"""

    name: str
    """"""


class Step(BaseModel):
    """Container for a single step"""

    class Config:
        """Config for the step"""

        arbitrary_types_allowed = True

    name: str
    """Name of step"""
    module: str
    """Module used in the step"""
    action: str
    """The command type to get executed by the robot"""
    args: Optional[Dict]
    """Arguments for instruction"""
    checks: Optional[str]
    """For future use"""
    requirements: Optional[Dict]
    """Equipment/resources needed in module"""
    dependencies: Optional[Union[str, UUID]]
    """Other steps required to be done before this can start"""
    priority: Optional[int]
    """For scheduling"""
    id: UUID = Field(default_factory=uuid4)
    """ID of step"""
    comment: Optional[str]
    """Notes about step"""

    # Assumes any path given to args is a yaml file
    # TODO consider if we want any other files given to the workflow files
    @validator("args")
    def validate_args_dict(cls, v, **kwargs):
        """asserts that args dict is assembled correctly"""
        assert isinstance(v, dict), "Args is not a dictionary"
        for key, arg_data in v.items():
            try:
                arg_path = Path(arg_data)
                # Strings can be path objects, so check if exists before loading it
                if arg_path.exists():
                    yaml.safe_load(arg_path.open("r"))
                    v[key] = yaml.safe_load(arg_path.open("r"))

            except TypeError:  # Is not a file
                pass

        return v


class Metadata(BaseModel):
    """Metadata container"""

    author: Optional[str]
    """Who authored this workflow"""
    info: Optional[str]
    """Long description"""
    version: float = 0.1
    """Version of interface used"""


class Workcell(BaseModel):
    """Container for information in a workcell"""

    name: str
    """Name of the workflow"""
    config: Optional[Dict[str, Any]]
    """Globus search index, needed for publishing"""
    modules: List[Module]
    """The modules available to a workcell"""
    locations: Optional[Dict[str, Any]]
    """Locations used by the workcell"""


class Workflow(BaseModel):
    """Grand container that pulls all info of a workflow together"""

    name: str
    """Name of the workflow"""
    modules: List[SimpleModule]
    """List of modules needed for the workflow"""
    flowdef: List[Step]
    """Steps of the flow"""
    metadata: Metadata
    """Information about the flow"""
    payload: Optional[Dict]
    """input information for a given workflow run"""


class StepStatus(Enum):
    """Status for a step of a workflow"""

    IDLE = "idle"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class NodeStatus(Enum):
    """Status for the state of a Node"""

    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    UNKNOWN = "unknown"
