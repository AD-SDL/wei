"""Types related to workflow steps"""

import json
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path, PureWindowsPath
from typing import Any, Dict, List, Optional
from zipfile import ZipFile

import yaml
from fastapi import UploadFile
from fastapi.responses import FileResponse
from pydantic import AliasChoices, Field, ValidationInfo, field_validator
from typing_extensions import Literal

from wei.types.base_types import BaseModel, PathLike, ulid_factory


class StepStatus(str, Enum):
    """Status for a step of a workflow"""

    IDLE = "idle"
    NOT_READY = "not_ready"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StepResponse(BaseModel):
    """
    Standard Response returned by module interfaces
    in response to action requests
    """

    status: StepStatus = StepStatus.SUCCEEDED
    """Whether the step succeeded or failed"""
    error: Optional[str] = None
    """Error message resulting from the action"""
    data: Optional[Dict[str, Any]] = None
    """Key value dict of data returned from step"""
    files: Optional[Dict[str, Any]] = None
    """Key value dict of file labels and file names from step"""

    def to_headers(self) -> Dict[str, str]:
        """Converts the response to a dictionary of headers"""
        return {
            "x-wei-status": str(self.status),
            "x-wei-data": json.dumps(self.data),
            "x-wei-error": json.dumps(self.error),
            "x-wei-files": json.dumps(self.files),
        }

    @classmethod
    def from_headers(cls, headers: Dict[str, Any]) -> "StepResponse":
        """Creates a StepResponse from the headers of a file response"""

        return cls(
            status=StepStatus(headers["x-wei-status"]),
            error=json.loads(headers["x-wei-error"]),
            files=json.loads(headers["x-wei-files"]),
            data=json.loads(headers["x-wei-data"]),
        )

    @classmethod
    def step_succeeded(
        cls, files: Dict[str, str] = None, data: Dict[str, str] = None
    ) -> "StepResponse":
        """Returns a StepResponse for a successful step"""
        return cls(status=StepStatus.SUCCEEDED, files=files, data=data)

    @classmethod
    def step_failed(cls, error: str = "") -> "StepResponse":
        """Returns a StepResponse for a failed step"""
        return cls(status=StepStatus.FAILED, error=error)

    @classmethod
    def step_not_ready(cls, error: str = "") -> "StepResponse":
        """Returns a StepResponse for a failed step"""
        return cls(status=StepStatus.NOT_READY, error=error)


class StepSucceeded(StepResponse):
    """A StepResponse for a successful step"""

    status: Literal[StepStatus.SUCCEEDED] = StepStatus.SUCCEEDED


class StepFailed(StepResponse):
    """A StepResponse for a failed step"""

    status: Literal[StepStatus.FAILED] = StepStatus.FAILED


class StepFileResponse(FileResponse):
    """
    Convenience wrapper for FastAPI's FileResponse class
    If not using FastAPI, return a response with:
    - The file object as the response content
    - The StepResponse parameters as custom headers, prefixed with "x-wei-"
    """

    def __init__(
        self,
        status: StepStatus,
        files: Dict[str, str],
        data: Dict[str, str] = None,
    ):
        """
        Returns a FileResponse with the given files as the response content
        """
        if len(files) == 1:
            return super().__init__(
                path=list(files.values())[0],
                headers=StepResponse(
                    status=status, files=files, data=data
                ).to_headers(),
            )

        temp = ZipFile("temp.zip", "w")
        for file in files:
            temp.write(files[file])
            files[file] = str(PureWindowsPath(files[file]).name)

        return super().__init__(
            path="temp.zip",
            headers=StepResponse(status=status, files=files, data=data).to_headers(),
        )


class Step(BaseModel, arbitrary_types_allowed=True):
    """Container for a single step"""

    """Step Definition"""

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
    comment: Optional[str] = None
    """Notes about step"""
    data_labels: Optional[Dict[str, str]] = None
    """Dictionary of user provided data labels"""

    """Runtime information"""

    id: str = Field(default_factory=ulid_factory)
    """ID of step"""
    start_time: Optional[datetime] = None
    """Time the step started running"""
    end_time: Optional[datetime] = None
    """Time the step finished running"""
    duration: Optional[timedelta] = None
    """Duration of the step's run"""
    result: Optional["StepResponse"] = None
    """Result of the step after being run"""

    # Load any yaml arguments
    @field_validator("args")
    @classmethod
    def validate_args_dict(cls, v: Any) -> Any:
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
