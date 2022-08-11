"""Dataclasses used for the workflows/cells"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Type, TypeVar, Union
from uuid import UUID, uuid4

import yaml
from pydantic import BaseModel as _BaseModel
from pydantic import Field

_T = TypeVar("_T")

PathLike = Union[str, Path]


class BaseModel(_BaseModel):
    """Allows any sub-class to inherit methods allowing for programatic description of protocols
    Can load a yaml into a class and write a class into a yaml file.
    """

    def write_yaml(self, cfg_path: PathLike) -> None:
        """Allows programatic creation of ot2util objects and saving them into yaml.
        Parameters
        ----------
        cfg_path : PathLike
            Path to dump the yaml file.
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

    name: str
    """name of the module, should be opentrons api compatible"""
    type: str
    """type of the robot (e.g OT2, pf400, etc.) """
    config: Dict  # contains ip and port
    """the necessary configuration for the robot, arbitrary dict"""
    positions: Optional[dict]
    """Optional, if the robot supports positions we will use htem"""
    tag: Optional[Tag]
    """Vision tag"""
    id: UUID = Field(default_factory=uuid4)
    """Robot id"""


class SimpleModule(BaseModel):
    """Simple module for use in the workflow file (does not need as much info)"""

    name: str
    """Name, should follow opentrons api standard"""
    type: str
    """Type of robot"""
    id: Optional[Union[UUID, str]]
    """Id of the robot, not necesary as this is stored in the workcell."""
    # what else? Equipemnt it needs?


class Action(BaseModel):
    """Container to store command information"""

    name: str
    """Name of the command"""
    instruction: str
    """The instruction to run"""
    args: Dict
    """Arguments for instruction"""
    checks: Optional[str]
    """For future use"""
    comment: Optional[str]
    """Note about the command, from user """


class Step(BaseModel):
    """Container for a single step"""

    name: str
    """Name of step"""
    module: str
    """Module used in the step"""
    actions: List[Action]
    """List of commands to be executed by the step"""
    requirements: Optional[Dict]
    """Equipment needed in module"""
    dependencies: Optional[Union[str, UUID]]
    """Other steps required to be done before this can start"""
    priority: Optional[int]
    """For scheduling"""
    id: UUID = Field(default_factory=uuid4)
    """ID of step"""
    comment: Optional[str]
    """Notes about step"""


class Metadata(BaseModel):
    """Metadata container"""

    name: Optional[str]
    """Name of workflow"""
    author: Optional[str]
    """Who authored this workflow"""
    info: Optional[str]
    """Long description"""
    version: float = 0.1
    """Version of interface used"""


class Workflow(BaseModel):
    """Grand container that pulls all info of a workflow together"""

    workcell: Union[str, Path]
    """The path to the workcell required by this workflow"""
    modules: List[SimpleModule]
    """List of modules needed for the workflow"""
    flowdef: List[Step]
    """Steps of the flow"""
    metadata: Metadata
    """Information about the flow"""


class WorkCell(BaseModel):
    """Container for information in a workcell"""

    modules: List[Module]
    """The modules available to a workcell"""
