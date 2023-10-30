"""Dataclasses used for the workflows/cells"""

import json
from enum import Enum
from pathlib import Path
from typing import Any, ClassVar, Dict, List, Optional, Type, TypeVar, Union

import ulid
import yaml
from fastapi.responses import FileResponse
from pydantic import BaseModel as _BaseModel
from pydantic import Field, validator

_T = TypeVar("_T")

PathLike = Union[str, Path]


class BaseModel(_BaseModel):
    """Allows any sub-class to inherit methods allowing for programmatic description of protocols
    Can load a yaml into a class and write a class into a yaml file.
    """

    class Config:
        """Config for the BaseModel"""

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
        return cls(**raw_data)  # type: ignore[call-arg]


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
    config: Dict
    """the necessary configuration for the robot, arbitrary dict"""
    positions: Optional[dict] = {}
    """Optional, if the robot supports positions we will use them"""
    tag: Optional[Tag] = None
    """Vision tag"""
    workcell_coordinates: Optional[List] = []
    """location in workcell"""
    active: Optional[bool] = True
    """Whether or not the robot is active"""

    # Runtime values
    id: str = Field(default=ulid.new().str)
    """Robot id"""
    state: Optional[ModuleStatus] = Field(default=ModuleStatus.INIT)
    """Current state of the module"""
    queue: Optional[List[str]] = []
    """Queue of workflows to be run at this location"""

    @property
    def location(self):
        """Alias for workcell_coordinates"""
        return self.workcell_coordinates

    @validator("config")
    def validate_config(cls, v, values, **kwargs):
        """Validate the config field of the workcell config with special rules for each type of robot"""
        config_validation = json.load(cls.config_validation.open())
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
    """standardizes communications with different daemons"""

    name: str
    """"""

    def send_action(self, action):
        """sends an action"""
        print(action)
        print("Send Action not implemented")
        return {}

    def get_about(
        self,
    ):
        """gets about information"""
        print("Get About not implemented")
        return {}

    def get_state(
        self,
    ):
        """gets the robot state"""
        print("Get State not implemented")
        return {}

    def get_resources(
        self,
    ):
        """gets the robot resources"""
        print("Get Resources not implemented")
        return {}


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
    args: Optional[Dict] = {}
    """Arguments for instruction"""
    checks: Optional[str] = None
    """For future use"""
    requirements: Optional[Dict] = {}
    """Equipment/resources needed in module"""
    dependencies: List[str] = []
    """Other steps required to be done before this can start"""
    priority: Optional[int] = None
    """For scheduling"""
    id: str = Field(default=ulid.new().str)
    """ID of step"""
    comment: Optional[str] = None
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
                    try:
                        yaml.safe_load(arg_path.open("r"))
                        v[key] = yaml.safe_load(arg_path.open("r"))
                    except IsADirectoryError:
                        pass
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
    config: Optional[Dict[str, Any]] = {}
    """Globus search index, needed for publishing"""
    modules: List[Module]
    """The modules available to a workcell"""
    locations: Optional[Dict[str, Any]] = {}
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
    flowdef: List[Union[Step, Dict]]
    """Steps of the flow"""
    metadata: Metadata = Field(default_factory=Metadata)
    """Information about the flow"""
    payload: Optional[Dict] = {}
    """input information for a given workflow run"""


class WorkflowRun(Workflow):
    """Container for a workflow run"""

    label: Optional[str] = None
    """Label for the workflow run"""
    run_id: str = Field(default=ulid.new().str)
    """ID of the workflow run"""
    status: WorkflowStatus = Field(default=WorkflowStatus.NEW)
    """current status of the workflow"""
    result: Dict = Field(default={})
    """result from the Workflow"""
    hist: Dict = Field(default={})
    """history of the workflow"""
    experiment_id: Optional[str] = None
    """ID of the experiment this workflow is a part of"""
    experiment_path: Optional[PathLike] = None
    """Path to the experiment this workflow is a part of"""
    step_index: int = 0
    """Index of the current step"""
    run_dir: Optional[PathLike] = None
    """Path to the run directory"""


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
            "X-WEI-action-response": str(self.action_response),
            "X-WEI-action-msg": self.action_msg,
            "X-WEI-action-log": self.action_log,
        }

    @classmethod
    def from_headers(cls, response: FileResponse):
        """Creates a StepResponse from the headers of a file response"""
        return cls(
            action_response=StepStatus(response.headers["X-WEI-action-response"]),
            action_msg=response.headers["X-WEI-action-msg"],
            action_log=response.headers["X-WEI-action-log"],
        )


class StepFileResponse(FileResponse):
    """
    Convenience wrapper for FastAPI's FileResponse class
    If not using FastAPI, return a response with
        - The file object as the response content
        - The StepResponse parameters as custom headers, prefixed with "wei_"
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


class ExperimentStatus(str, Enum):
    """Status for an experiment"""

    FAILED = "failed"
    CREATED = "created"


class Location(BaseModel):
    """Container for a location"""

    name: str
    """Name of the location"""
    workcell_coordinates: Any
    """Coordinates of the location"""
    state: Optional[str] = "Empty"
    """State of the location"""
    queue: Optional[List[str]] = []
    """Queue of workflows to be run at this location"""
