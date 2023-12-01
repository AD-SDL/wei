"""Dataclasses used for the workflows/cells"""

import json
from enum import Enum
from pathlib import Path
from typing import Any, ClassVar, Dict, List, Optional, Tuple, Type, TypeVar, Union

import ulid
import yaml
from fastapi.responses import FileResponse
from pydantic import BaseModel as _BaseModel
from pydantic import Field, computed_field, field_serializer, validator

from wei.core.experiment import Experiment

_T = TypeVar("_T")

PathLike = Union[str, Path]


def ulid_factory() -> str:
    """Generates a ulid string"""
    return ulid.new().str


class BaseModel(_BaseModel):
    """Allows any sub-class to inherit methods allowing for programmatic description of protocols
    Can load a yaml into a class and write a class into a yaml file.
    """

    class Config:
        """config for the BaseModel"""

        use_enum_values = True  # Needed to serialize/deserialize enums

    def write_yaml(self, cfg_path: PathLike) -> None:
        """Allows programmatic creation of ot2util objects and saving them into yaml.
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
        return cls(**raw_data)


class Tag(BaseModel):
    """Vision tag"""

    type: str
    """Type of the tag"""
    id: str  # not quite sure what this will be
    """Id of the tag """


class ModuleStatus(str, Enum):
    """Status for the state of a Module"""

    INIT = "INIT"
    IDLE = "IDLE"
    BUSY = "BUSY"
    ERROR = "ERROR"
    UNKNOWN = "UNKNOWN"


class Module(BaseModel):
    """Container for a module found in a workcell file (more info than in a workflow file)"""

    # Hidden
    config_validation: ClassVar[Path] = (
        Path(__file__).parent.resolve() / "data/module_configs_validation.json"
    )

    # Public
    name: str
    """name of the module, should be opentrons api compatible"""
    model: Optional[str] = None
    """type of the robot (e.g OT2, pf400, etc.) """
    interface: str
    """Type of client (e.g ros_wei_client)"""
    config: Dict[str, Any] = {}
    """the necessary configuration for the robot, arbitrary dict"""
    locations: List[str] = []
    """Optional, associates named locations with a module"""
    tag: Optional[Tag] = None
    """Vision tag"""
    workcell_coordinates: Optional[Any] = None
    """location in workcell"""
    active: Optional[bool] = True
    """Whether or not the robot is active"""

    # Runtime values
    id: str = Field(default_factory=ulid_factory)
    """Robot id"""
    state: ModuleStatus = Field(default=ModuleStatus.INIT)
    """Current state of the module"""
    queue: List[str] = []
    """Queue of workflows to be run at this location"""

    @property
    def location(self) -> Any:
        """Alias for workcell_coordinates"""
        return self.workcell_coordinates

    @validator("config")
    def validate_config(cls, v: Any, values: Dict[str, Any], **kwargs: Any) -> Any:
        """Validate the config field of the workcell config with special rules for each module interface"""
        from wei.core.interface import InterfaceMap

        interface_type = str(values.get("interface", "")).lower()

        if interface_type.lower() not in InterfaceMap.interfaces:
            raise ValueError(
                f"Interface '{interface_type}' for module {values.get('name')} is invalid"
            )

        if InterfaceMap.interfaces[interface_type].config_validator(v):
            return v
        else:
            raise ValueError(
                f"Config for interface '{interface_type}' is invalid for module {values.get('name')}"
            )


class SimpleModule(BaseModel):
    """Simple module for use in the workflow file (does not need as much info)"""

    name: str
    """Name, should correspond with a module ros node"""


class Interface(BaseModel):
    """standardizes communications with various module interface implementations"""

    name: str
    """"""

    @staticmethod
    def send_action(
        step: "Step", module: Module, **kwargs: Any
    ) -> Tuple[str, str, str]:
        """sends an action"""
        raise NotImplementedError()

    @staticmethod
    def get_about(module: Module, **kwargs: Any) -> Any:
        """gets about information"""
        raise NotImplementedError()

    @staticmethod
    def get_state(module: Module, **kwargs: Any) -> Any:
        """gets the robot state"""
        raise NotImplementedError()

    @staticmethod
    def get_resources(module: Module, **kwargs: Any) -> Any:
        """gets the robot resources"""
        raise NotImplementedError()


class Step(BaseModel):
    """Container for a single step"""

    class Config:
        """config for the step"""

        arbitrary_types_allowed = True

    name: str
    """Name of step"""
    module: str
    """Module used in the step"""
    action: str
    """The command type to get executed by the robot"""
    args: Dict[str, Any] = {}
    """Arguments for instruction"""
    checks: Optional[str] = None
    """For future use"""
    locations: Dict[str, Any] = {}
    """locations referenced in the step"""
    requirements: Dict[str, Any] = {}
    """Equipment/resources needed in module"""
    dependencies: List[str] = []
    """Other steps required to be done before this can start"""
    priority: Optional[int] = None
    """For scheduling"""
    id: str = Field(default_factory=ulid_factory)
    """ID of step"""
    comment: Optional[str] = None
    """Notes about step"""

    # Load any yaml arguments
    @validator("args")
    def validate_args_dict(cls, v: Any, **kwargs: Any) -> Any:
        """asserts that args dict is assembled correctly"""
        assert isinstance(v, dict), "Args is not a dictionary"
        for key, arg_data in v.items():
            try:
                arg_path = Path(arg_data)
                # Strings can be path objects, so check if exists before loading it
                if arg_path.exists() and (
                    arg_path.suffix == ".yaml" or arg_path.suffix == ".yml"
                ):
                    yaml.safe_load(arg_path.open("r"))
                    v[key] = yaml.safe_load(arg_path.open("r"))
            except TypeError:  # Is not a file
                pass

        return v


class Metadata(BaseModel):
    """Metadata container"""

    author: Optional[str] = None
    """Who authored this workflow"""
    info: Optional[str] = None
    """Long description"""
    version: float = 0.1
    """Version of interface used"""


class WorkcellData(BaseModel):
    """Container for information in a workcell"""

    name: str
    """Name of the workflow"""
    config: Dict[str, Any] = {}
    """Globus search index, needed for publishing"""
    modules: List[Module]
    """The modules available to a workcell"""
    locations: Dict[str, Any] = {}
    """Locations used by the workcell"""


class WorkflowStatus(str, Enum):
    """Status for a workflow run"""

    NEW = "new"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    UNKNOWN = "unknown"


class Workflow(BaseModel):
    """Grand container that pulls all info of a workflow together"""

    name: str
    """Name of the workflow"""
    modules: List[SimpleModule]
    """List of modules needed for the workflow"""
    flowdef: List[Step]
    """User Submitted Steps of the flow"""
    metadata: Metadata = Field(default_factory=Metadata)
    """Information about the flow"""


class WorkflowRun(Workflow):
    """Container for a workflow run"""

    label: Optional[str] = None
    """Label for the workflow run"""
    run_id: str = Field(default_factory=ulid_factory)
    """ID of the workflow run"""
    payload: Dict[str, Any] = {}
    """input information for a given workflow run"""
    status: WorkflowStatus = Field(default=WorkflowStatus.NEW)
    """current status of the workflow"""
    steps: List[Step] = []
    """WEI Processed Steps of the flow"""
    result: Dict[str, Any] = Field(default={})
    """result from the Workflow"""
    hist: Dict[str, Any] = Field(default={})
    """history of the workflow"""
    experiment_id: str = ""
    """ID of the experiment this workflow is a part of"""
    step_index: int = 0
    """Index of the current step"""
    simulate: bool = False
    """Whether or not this workflow is being simulated"""

    @computed_field  # type: ignore
    @property
    def run_dir(self) -> Path:
        """Path to the run directory"""
        return Path(
            Experiment(experiment_id=self.experiment_id).run_dir,
            f"{self.name}_{self.run_id}",
        )

    @computed_field  # type: ignore
    @property
    def run_log(self) -> Path:
        """Path to the run directory"""
        return Path(
            self.run_dir,
            self.run_id + "_run_log.log",
        )

    @computed_field  # type: ignore
    @property
    def result_dir(self) -> Path:
        """Path to the result directory"""
        return Path(self.run_dir, "results")

    @field_serializer("run_dir")
    def _serialize_run_dir(self, run_dir: Path) -> str:
        return str(run_dir)

    @field_serializer("result_dir")
    def _serialize_result_dir(self, result_dir: Path) -> str:
        return str(result_dir)

    @field_serializer("run_log")
    def _serialize_run_log(self, run_log: Path) -> str:
        return str(run_log)


class StepStatus(str, Enum):
    """Status for a step of a workflow"""

    IDLE = "idle"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class StepResponse(BaseModel):
    """
    Standard Response returned by module interfaces
    in response to action requests
    """

    action_response: StepStatus = StepStatus.SUCCEEDED
    """Whether the action succeeded, failed, is running, or is idle"""
    action_msg: str = ""
    """Any result from the action. If the result is a file, this should be the file name"""
    action_log: str = ""
    """Error or log messages resulting from the action"""

    def to_headers(self) -> Dict[str, str]:
        """Converts the response to a dictionary of headers"""
        return {
            "x-wei-action_response": str(self.action_response),
            "x-wei-action_msg": self.action_msg,
            "x-wei-action_log": self.action_log,
        }

    @classmethod
    def from_headers(cls, headers: Dict[str, Any]) -> "StepResponse":
        """Creates a StepResponse from the headers of a file response"""

        return cls(
            action_response=StepStatus(headers["x-wei-action_response"]),
            action_msg=headers["x-wei-action_msg"],
            action_log=headers["x-wei-action_log"],
        )


class StepFileResponse(FileResponse):
    """
    Convenience wrapper for FastAPI's FileResponse class
    If not using FastAPI, return a response with
        - The file object as the response content
        - The StepResponse parameters as custom headers, prefixed with "x-wei-"
    """

    def __init__(self, action_response: StepStatus, action_log: str, path: PathLike):
        """
        Returns a FileResponse with the given path as the response content
        """
        return super().__init__(
            path=path,
            headers=StepResponse(
                action_response=action_response,
                action_msg=str(path),
                action_log=action_log,
            ).to_headers(),
        )


class Location(BaseModel):
    """Container for a location"""

    name: str
    """Name of the location"""
    coordinates: Dict[str, Any]
    """Coordinates of the location"""
    state: str = "Empty"
    """State of the location"""
    queue: List[str] = []
    """Queue of workflows to be run at this location"""


class Event(BaseModel):
    """A single event in an experiment"""

    experiment_id: str
    event_type: str
    event_name: str
    event_info: Optional[Any] = None
