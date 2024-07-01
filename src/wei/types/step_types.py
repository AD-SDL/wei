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


class DataPoint(BaseModel):
    """An object to containt and locate data identified by modules"""

    label: str
    """label of this data point"""
    step_id: Optional[str] = None
    """step that generated the data point"""
    workflow_id: Optional[str] = None
    """workflow that generated the data point"""
    experiment_id: Optional[str] = None
    """experiment that generated the data point"""
    type: str = "base"
    """type of the datapoint, inherited from class"""
    campaign_id: Optional[str] = None
    """campaign of the data point"""
    id: str = Field(default_factory=ulid_factory)
    """specific id for this data point"""


class LocalFileDataPoint(DataPoint):
    """a datapoint containing a file"""

    type: str = "local_file"
    """local file"""
    path: str
    """path to the file"""


class ValueDataPoint(DataPoint):
    """a datapoint contained in the Json value"""

    type: str = "data_value"
    """data_value"""
    value: Any
    """value of the data point"""


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

    status: StepStatus = StepStatus.SUCCEEDED
    """Whether the step succeeded or failed"""
    error: Optional[str] = None
    """Error message resulting from the action"""
    data: Optional[dict] = None
    """Key value dict of data returned from step"""
    files: Optional[dict] = None
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
    def step_failed(cls, error: str) -> "StepResponse":
        """Returns a StepResponse for a failed step"""
        return cls(error=error)


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
        path: PathLike = None,
        data: Dict[str, str] = None,
    ):
        """
        Returns a FileResponse with the given path as the response content
        """
        if path is None:
            path = files[list(files.keys())[0]]
        return super().__init__(
            path=path,
            headers=StepResponse(status=status, files=files, data=data).to_headers(),
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
    data_labels: Optional[Dict[str, str]] = None
    """Dictionary of user provided data labels"""
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


class DataPointLocation(str, Enum):
    """Status for a step of a workflow"""

    LOCALFILE = "local_file"
    VALUE = "data_value"
