"""Types related to workflows"""

from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import Field, field_validator

from wei.types.base_types import BaseModel, Metadata, ulid_factory
from wei.types.module_types import SimpleModule
from wei.types.step_types import Step


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

    @property
    def is_active(self) -> bool:
        """Whether or not the workflow run is active"""
        return self in [
            WorkflowStatus.NEW,
            WorkflowStatus.QUEUED,
            WorkflowStatus.RUNNING,
            WorkflowStatus.IN_PROGRESS,
            WorkflowStatus.PAUSED,
        ]


class WorkflowParameter(BaseModel):
    """container for a workflow parameter"""

    name: str
    """the name of the parameter"""
    default: Optional[Any] = None
    """ the default value of the parameter"""


class Workflow(BaseModel):
    """Grand container that pulls all info of a workflow together"""

    name: str
    """Name of the workflow"""
    metadata: Metadata = Field(default_factory=Metadata)
    """Information about the flow"""
    parameters: Optional[List[WorkflowParameter]] = []
    """Inputs to the workflow"""
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

    @field_validator("flowdef", mode="after")
    @classmethod
    def ensure_data_label_uniqueness(cls, v: Any) -> Any:
        """Ensure that the names of the arguments and files are unique"""
        labels = []
        for step in v:
            if step.data_labels:
                for key in step.data_labels:
                    if step.data_labels[key] in labels:
                        raise ValueError("Data labels must be unique across workflow")
                    else:
                        labels.append(step.data_labels[key])
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
    experiment_id: str
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

    def get_step_by_name(self, name: str) -> Step:
        """Return the step object by its name"""
        for step in self.steps:
            if step.name == name:
                return step
        raise KeyError(f"Step {name} not found in workflow run {self.run_id}")

    def get_step_by_id(self, id: str) -> Step:
        """Return the step object indexed by its id"""
        for step in self.steps:
            if step.id == id:
                return step
        raise KeyError(f"Step {id} not found in workflow run {self.run_id}")

    def get_datapoint_id_by_label(self, label: str) -> str:
        """Return the ID of the first datapoint with the given label in a workflow run"""
        for step in self.steps:
            if step.result.data:
                for key in step.result.data:
                    if key == label:
                        return step.result.data[key]
        raise KeyError(f"Label {label} not found in workflow run {self.run_id}")

    def get_all_datapoint_ids_by_label(self, label: str) -> List[str]:
        """Return the IDs of all datapoints with the given label in a workflow run"""
        ids = []
        for step in self.steps:
            if step.result.data:
                for key in step.result.data:
                    if key == label:
                        ids.append(step.result.data[key])
        if not ids:
            raise KeyError(f"Label {label} not found in workflow run {self.run_id}")
        return ids
