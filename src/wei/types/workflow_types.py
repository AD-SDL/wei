"""Types related to workflows"""

from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import Field, field_validator

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
    """Newly created workflow run, hasn't been queued yet"""
    QUEUED = "queued"
    """Workflow run is queued, hasn't started yet"""
    RUNNING = "running"
    """Workflow is currently running a step"""
    IN_PROGRESS = "in_progress"
    """Workflow run has started, but is not actively running a step"""
    PAUSED = "paused"
    """Workflow run is paused"""
    COMPLETED = "completed"
    """Workflow run has completed"""
    FAILED = "failed"
    """Workflow run has failed"""
    UNKNOWN = "unknown"
    """Workflow run status is unknown"""
    CANCELLED = "cancelled"
    """Workflow run has been cancelled"""


class Workflow(BaseModel):
    """Grand container that pulls all info of a workflow together"""

    name: str
    """Name of the workflow"""
    metadata: Metadata = Field(default_factory=Metadata)
    """Information about the flow"""
    flowdef: List[Step]
    """User Submitted Steps of the flow"""

    modules: List[Union[str, SimpleModule]] = []
    """DEPRECATED: List of modules needed for the workflow.
    These are no longer validated or required, but the key remains to support legacy workflows."""

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
