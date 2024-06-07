"""Types related to workflow steps"""

import json
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from fastapi import UploadFile
from fastapi.responses import FileResponse
from pydantic import AliasChoices, Field, ValidationInfo, field_validator, validator

from wei.types.base_types import BaseModel, PathLike, ulid_factory


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

    @classmethod
    def step_succeeded(cls, action_msg: str, action_log: str = "") -> "StepResponse":
        """Returns a StepResponse for a successful step"""
        return cls(
            action_response=StepStatus.SUCCEEDED,
            action_msg=action_msg,
            action_log=action_log,
        )

    @classmethod
    def step_failed(cls, action_log: str, action_msg: str = "") -> "StepResponse":
        """Returns a StepResponse for a failed step"""
        return cls(
            action_response=StepStatus.FAILED,
            action_msg=action_msg,
            action_log=action_log,
        )


class StepFileResponse(FileResponse):
    """
    Convenience wrapper for FastAPI's FileResponse class
    If not using FastAPI, return a response with:
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


class Step(BaseModel, arbitrary_types_allowed=True):
    """Container for a single step"""

    name: str
    """Name of step"""
    module: str
    """Module used in the step"""
    action: str
    """The command type to get executed by the robot"""
    args: Dict[str, Any] = {}
    """Arguments for instruction"""
    files: Dict[str, PathLike] = {}
    """Files to be used in the step"""
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

    start_time: Optional[datetime] = None
    """Time the step started running"""
    end_time: Optional[datetime] = None
    """Time the step finished running"""
    duration: Optional[timedelta] = None
    """Duration of the step's run"""
    result: Optional["StepResponse"] = None
    """Result of the step after being run"""

    # Load any yaml arguments
    @validator("args")
    def validate_args_dict(cls, v: Any, **kwargs: Any) -> Any:
        """asserts that args dict is assembled correctly"""
        assert isinstance(v, dict), "Args is not a dictionary"
        for key, arg_data in v.items():
            try:
                arg_path = Path(arg_data)
                # Strings can be path objects, so check if exists before loading it
                if not arg_path.exists():
                    return v
                else:
                    print(arg_path)
                    print(arg_path.suffix)
                if arg_path.suffix == ".yaml" or arg_path.suffix == ".yml":
                    print(f"Loading yaml from {arg_path}")
                    v[key] = yaml.safe_load(arg_path.open("r"))
                    print(v[key])
            except TypeError:  # Is not a file
                pass

        return v


class ActionRequest(BaseModel):
    """Request to perform an action on a module"""

    name: str = Field(
        alias=AliasChoices("action_handle", "name"),
    )
    """Name of the action to perform"""
    args: Optional[Dict[str, Any]] = Field(alias=AliasChoices("action_vars", "args"))
    """Arguments for the action"""
    files: List[UploadFile] = []
    """Files to be sent along with the action"""

    @field_validator("args", mode="before")
    @classmethod
    def validate_args(cls, v: Any, info: ValidationInfo) -> Any:
        """Validate the args field of the action request"""
        if isinstance(v, str):
            v = json.loads(v)
        if v is None:
            return {}
        return v
