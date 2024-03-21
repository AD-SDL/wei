"""Types related to workflows"""

from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import (
    Field,
    computed_field,
    field_serializer,
    field_validator,
)

from wei.core.experiment import get_experiment_runs_dir
from wei.types.base_types import BaseModel, ulid_factory
from wei.types.module_types import SimpleModule
from wei.types.step_types import Step


class Metadata(BaseModel, extra="allow"):
    """Metadata container"""

    author: Optional[str] = None
    """Who authored this workflow"""
    info: Optional[str] = None
    """Long description"""
    version: float = 0.1
    """Version of interface used"""


class WorkflowStatus(str, Enum):
    """Status for a workflow run"""

    NEW = "new"
    QUEUED = "queued"
    RUNNING = "running"
    WAITING = "waiting"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    UNKNOWN = "unknown"


class Workflow(BaseModel):
    """Grand container that pulls all info of a workflow together"""

    name: str
    """Name of the workflow"""
    modules: List[str | SimpleModule]
    """List of modules needed for the workflow"""
    flowdef: List[Step]
    """User Submitted Steps of the flow"""
    metadata: Metadata = Field(default_factory=Metadata)
    """Information about the flow"""

    @field_validator("modules", mode="after")
    def validate_modules(cls, v) -> str:
        """Converts SimpleModule objects to strings"""
        for i in range(len(v)):
            if isinstance(v[i], SimpleModule):
                v[i] = v[i].name
        return v


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

    start_time: Optional[datetime] = None
    """Time the workflow started running"""
    end_time: Optional[datetime] = None
    """Time the workflow finished running"""
    duration: Optional[timedelta] = None
    """Duration of the workflow's run"""

    @computed_field  # type: ignore
    @property
    def run_dir(self) -> Path:
        """Path to the run directory"""
        return Path(
            get_experiment_runs_dir(self.experiment_id) / f"{self.name}_{self.run_id}"
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
