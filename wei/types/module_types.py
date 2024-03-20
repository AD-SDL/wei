"""Types related to Modules"""

from enum import Enum
from pathlib import Path
from typing import Any, ClassVar, Dict, List, Optional, Tuple, Union

from pydantic import (
    AliasChoices,
    Field,
    validator,
)

from wei.types.base_types import BaseModel, ulid_factory
from wei.types.step_types import Step


class AdminCommands(str, Enum):
    """Valid Admin Commands to send to a Module"""

    ESTOP = "estop"
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


class ModuleActionArg(BaseModel):
    """Defines an argument for a module action"""

    name: str
    """Name of the argument"""
    type: Union[str, List[str]]
    """Supported Type(s) of the argument"""
    default: Optional[Any] = None
    """Default value of the argument"""
    required: Optional[bool] = True
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
    """Defines an action that a module can perform"""

    name: str
    """Name of the action"""
    args: List[ModuleActionArg]
    """Arguments for the action"""
    files: Optional[List[ModuleActionFile]] = []
    """Files to be sent along with the action"""


class ModuleAbout(BaseModel):
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
    resource_pools: Optional[List[Any]] = Field(
        alias=AliasChoices("resources", "resource_pools"), alias_priority=2
    )
    """List of resource pools used by the module"""
    admin_commands: Optional[List[AdminCommands]] = []
    """List of admin commands supported by the module"""


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
    workcell_coordinates: Optional[Any] = Field(
        alias=AliasChoices("location", "workcell_coordinates"),
        alias_priority=2,
        default=None,
    )
    """location in workcell"""
    active: Optional[bool] = True
    """Whether or not the robot is active"""

    # Runtime values
    id: str = Field(default_factory=ulid_factory)
    """Robot id"""
    state: ModuleStatus = Field(default=ModuleStatus.INIT)
    """Current state of the module"""
    reserved: Optional[str] = None
    """ID of WorkflowRun that will run next on this Module"""
    about: Optional[Any] = None
    """About information for the module"""

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
