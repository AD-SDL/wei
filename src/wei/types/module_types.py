"""Types related to Modules"""

from enum import Enum
from typing import Any, Dict, Generic, List, Optional, Tuple, TypeVar, Union

from pydantic import (
    AliasChoices,
    Field,
    ValidationError,
    field_validator,
    model_validator,
)
from typing_extensions import Self

from wei.types.base_types import BaseModel, ulid_factory
from wei.types.step_types import Step

T = TypeVar("T")


class Location(Generic[T]):
    """A wrapper for Location objects for type hinting"""

    pass


class AdminCommands(str, Enum):
    """Valid Admin Commands to send to a Module"""

    SAFETY_STOP = "estop"
    RESET = "reset"
    PAUSE = "pause"
    RESUME = "resume"
    CANCEL = "cancel"
    SHUTDOWN = "shutdown"


class ModuleStatus(str, Enum):
    """Status for the state of a Module"""

    INIT = "INIT"
    IDLE = "IDLE"
    BUSY = "BUSY"
    ERROR = "ERROR"
    UNKNOWN = "UNKNOWN"
    PAUSED = "PAUSED"


class ModuleState(BaseModel, extra="allow"):
    """Model for the state of a Module"""

    status: ModuleStatus
    """Current state of the module"""
    error: Optional[str] = None
    """Error message if the module is in an error state"""


class LegacyModuleState(BaseModel, extra="allow"):
    """Legacy model for the state of a Module"""

    State: ModuleStatus

    def to_modern(self) -> ModuleState:
        """Converts the LegacyModuleState to a ModuleStatus"""
        return ModuleState(status=self.State)


class ModuleActionArg(BaseModel):
    """Defines an argument for a module action"""

    name: str
    """Name of the argument"""
    type: Union[str, List[str]]
    """Supported Type(s) of the argument"""
    default: Optional[Any] = None
    """Default value of the argument"""
    required: bool = True
    """Whether or not the argument is required"""
    description: str = ""
    """Description of the argument"""


class ModuleActionFile(BaseModel):
    """Defines a file for a module action"""

    name: str
    """Name of the file"""
    required: bool = True
    """Whether or not the file is required"""
    description: str = ""
    """Description of the file"""


class ModuleAction(BaseModel):
    """Defines an action that a module can perform."""

    name: str
    """Name of the action"""
    args: List[ModuleActionArg] = []
    """Arguments for the action"""
    description: Optional[str] = ""
    """A description of the action"""
    files: List[ModuleActionFile] = []
    """Files to be sent along with the action"""
    function: Optional[Any] = Field(default=None, exclude=True)
    """Function to be called when the action is executed. This must be a callable."""

    @field_validator("function", mode="after")
    @classmethod
    def validate_function(cls, v: Any) -> Optional[Any]:
        """Validate the function field of the ModuleAction"""
        if v is None:
            return v
        if callable(v):
            return v
        else:
            raise ValidationError("Function must be callable.")

    @model_validator(mode="after")
    @classmethod
    def ensure_name_uniqueness(cls, v: Any) -> Any:
        """Ensure that the names of the arguments and files are unique"""
        names = set()
        for arg in v.args:
            if arg.name in names:
                raise ValueError(f"Action name '{arg.name}' is not unique")
            names.add(arg.name)
        for file in v.files:
            if file.name in names:
                raise ValueError(f"File name '{file.name}' is not unique")
            names.add(file.name)
        return v


class ModuleAbout(BaseModel, extra="ignore"):
    """Defines how modules should reply on the /about endpoint"""

    name: str
    """Name of the module"""
    model: Optional[str] = None
    """Model of the module"""
    interface: Optional[str] = None
    """Interface used by the module"""
    version: Optional[str] = None
    """Version of the module"""
    description: Optional[str] = None
    """Description of the module"""
    actions: List[ModuleAction]
    """List of actions supported by the module"""
    resource_pools: List[Any] = Field(
        alias=AliasChoices("resources", "resource_pools"), alias_priority=2, default=[]
    )
    """List of resource pools used by the module"""
    admin_commands: List[AdminCommands] = []
    """List of admin commands supported by the module"""


class ModuleDefinition(BaseModel):
    """Static definition of a module, as used in a workcell file"""

    name: str
    """name of the module, should be opentrons api compatible"""
    model: Optional[str] = None
    """type of the robot (e.g OT2, pf400, etc.) """
    interface: str = "wei_rest_interface"
    """Type of client (e.g wei_ros_interface, wei_rest_interface, etc.)"""
    config: Dict[str, Any] = {}
    """the necessary configuration for the robot, arbitrary dict validated by `validate_config`"""
    locations: List[str] = []
    """Optional, associates named locations with a module"""
    workcell_coordinates: Optional[Any] = Field(
        alias=AliasChoices("location", "workcell_coordinates"),
        alias_priority=2,
        default=None,
    )
    """location in workcell"""
    active: Optional[bool] = True
    """Whether or not the device is active (set to False to disable)"""

    @model_validator(mode="after")
    def validate_config_against_interface(self) -> Self:
        """Ensure that the config field is valid for the specified interface"""
        from wei.types.interface_types import InterfaceMap

        interface_type = self.interface.lower()

        if interface_type not in InterfaceMap.interfaces:
            raise ValueError(
                f"Interface '{interface_type}' for module {self.name} is invalid"
            )

        if not InterfaceMap.interfaces[interface_type].config_validator(self.config):
            raise ValueError(
                f"Config for interface '{interface_type}' is invalid for module {self.name}"
            )

        return self


class Module(ModuleDefinition):
    """Live instance of a Module"""

    id: str = Field(default_factory=ulid_factory)
    """ID of this instance of a Module"""
    state: ModuleState = Field(default=ModuleState(status=ModuleStatus.UNKNOWN))
    """Current state of the module"""
    reserved: Optional[str] = None
    """ID of WorkflowRun that will run next on this Module"""
    about: Optional[ModuleAbout] = None
    """About information for the module"""


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
