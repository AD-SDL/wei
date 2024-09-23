"""Types related to Events"""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import Field

from wei.types.base_types import BaseModel, ulid_factory
from wei.types.experiment_types import Campaign, Experiment
from wei.types.step_types import Step
from wei.types.workcell_types import Workcell
from wei.types.workflow_types import WorkflowRun


class Event(BaseModel, extra="allow"):
    """A single event in an experiment"""

    event_id: str = Field(default_factory=ulid_factory)
    event_timestamp: datetime = Field(default_factory=datetime.now)
    experiment_id: Optional[str] = None
    campaign_id: Optional[str] = None
    workcell_id: Optional[str] = None
    event_type: str
    event_name: str

    event_info: Optional[Any] = None
    """Any additional information about the event (mostly kept for backwards compatibility)"""


class CampaignStartEvent(Event):
    """Event for creating a campaign"""

    event_type: Literal["CAMPAIGN"] = "CAMPAIGN"
    event_name: Literal["CREATE"] = "CREATE"

    campaign: Campaign
    """The campaign that was started"""


class ExperimentStartEvent(Event):
    """Event for starting an experiment"""

    event_type: Literal["EXPERIMENT"] = "EXPERIMENT"
    event_name: Literal["START"] = "START"

    experiment: Experiment
    """The experiment that started"""


class ExperimentContinueEvent(Event):
    """Event for continuing an experiment"""

    event_type: Literal["EXPERIMENT"] = "EXPERIMENT"
    event_name: Literal["CONTINUE"] = "CONTINUE"

    experiment: Optional[Experiment] = None
    """The experiment that was resumed"""


class ExperimentEndEvent(Event):
    """Event for ending an experiment"""

    event_type: Literal["EXPERIMENT"] = "EXPERIMENT"
    event_name: Literal["END"] = "END"

    experiment: Optional[Experiment] = None
    """The experiment that ended"""


class ExperimentDataPointEvent(Event):
    """Event for a data point in an experiment"""

    event_type: Literal["EXPERIMENT"] = "EXPERIMENT"
    event_name: Literal["DATA_POINT"] = "DATA_POINT"

    data_point: Dict[str, Any]
    """The data point being logged"""


class DecisionEvent(Event):
    """Event for a decision"""

    event_type: Literal["EXPERIMENT"] = "EXPERIMENT"
    event_name: Literal["DECISION"] = "DECISION"
    decision_name: str
    """The name of the decision made"""
    decision_value: Optional[bool] = None
    """The reason for the decision"""


class CommentEvent(Event):
    """Event for a comment"""

    event_type: Literal["EXPERIMENT"] = "EXPERIMENT"
    event_name: Literal["COMMENT"] = "COMMENT"

    comment: str
    """The comment"""


class LocalComputeEvent(Event):
    """Event for a local computation"""

    event_type: Literal["EXPERIMENT"] = "EXPERIMENT"
    event_name: Literal["LOCAL_COMPUTE"] = "LOCAL_COMPUTE"

    function_name: str
    """The name of the function called"""
    args: Optional[List[Any]] = None
    """The positional args passed to the function"""
    kwargs: Optional[Dict[str, Any]] = None
    """The keyword args passed to the function"""
    result: Optional[Any] = None
    """The result of the computation"""


class GlobusComputeEvent(Event):
    """Event for a globus computation"""

    event_type: Literal["EXPERIMENT"] = "EXPERIMENT"
    event_name: Literal["GLOBUS_COMPUTE"] = "GLOBUS_COMPUTE"

    function_name: str
    """The name of the function called"""
    args: Optional[List[Any]] = None
    """The positional args passed to the function"""
    kwargs: Optional[Dict[str, Any]] = None
    """The keyword args passed to the function"""
    result: Optional[Any] = None
    """The result of the computation"""


class GladierFlowEvent(Event):
    """Event for a Gladier Flow"""

    event_type: Literal["EXPERIMENT"] = "EXPERIMENT"
    event_name: Literal["GLADIER_FLOW"] = "GLADIER_FLOW"

    flow_name: str
    """The name of the flow"""
    flow_id: str
    """The ID of the flow"""


class LoopStartEvent(Event):
    """Event for the start of a loop"""

    event_type: Literal["EXPERIMENT"] = "EXPERIMENT"
    event_name: Literal["LOOP_START"] = "LOOP_START"

    loop_name: str
    """The name of the loop"""


class LoopEndEvent(Event):
    """Event for the end of a loop"""

    event_type: Literal["EXPERIMENT"] = "EXPERIMENT"
    event_name: Literal["LOOP_END"] = "LOOP_END"

    loop_name: str
    """The name of the loop"""


class LoopCheckEvent(Event):
    """Event for the conditional check of a loop"""

    event_type: Literal["EXPERIMENT"] = "EXPERIMENT"
    event_name: Literal["LOOP_CHECK"] = "LOOP_CHECK"

    loop_name: str
    """The name of the loop"""
    conditional: str
    """The conditional that was checked"""
    result: bool


class WorkcellStartEvent(Event):
    """Event for the start of a workcell"""

    event_type: Literal["WORKCELL"] = "WORKCELL"
    event_name: Literal["START"] = "START"

    workcell: Workcell
    """The workcell that was started"""


class WorkflowQueuedEvent(Event):
    """Event for a workflow being queued"""

    event_type: Literal["WORKFLOW"] = "WORKFLOW"
    event_name: Literal["QUEUED"] = "QUEUED"

    run_id: str
    """The ID of the workflow"""
    workflow_name: str
    """The name of the workflow"""

    @classmethod
    def from_wf_run(cls, wf_run: WorkflowRun) -> "WorkflowQueuedEvent":
        """Create a new workflow queued event"""
        return WorkflowQueuedEvent(
            experiment_id=wf_run.experiment_id,
            run_id=wf_run.run_id,
            workflow_name=wf_run.name,
        )


class WorkflowStartEvent(Event):
    """Event for a workflow starting"""

    event_type: Literal["WORKFLOW"] = "WORKFLOW"
    event_name: Literal["START"] = "START"

    run_id: str
    """The ID of the workflow"""
    workflow_name: str
    """The name of the workflow"""

    @classmethod
    def from_wf_run(cls, wf_run: WorkflowRun) -> "WorkflowStartEvent":
        """Create a new workflow start event"""
        return WorkflowStartEvent(
            experiment_id=wf_run.experiment_id,
            run_id=wf_run.run_id,
            workflow_name=wf_run.name,
        )


class WorkflowFailedEvent(Event):
    """Event for a workflow failing"""

    event_type: Literal["WORKFLOW"] = "WORKFLOW"
    event_name: Literal["FAILED"] = "FAILED"

    run_id: str
    """The ID of the workflow"""
    workflow_name: str
    """The name of the workflow"""

    @classmethod
    def from_wf_run(cls, wf_run: WorkflowRun) -> "WorkflowFailedEvent":
        """Create a new workflow failed event"""
        return WorkflowFailedEvent(
            experiment_id=wf_run.experiment_id,
            run_id=wf_run.run_id,
            workflow_name=wf_run.name,
        )


class WorkflowCompletedEvent(Event):
    """Event for a workflow completing"""

    event_type: Literal["WORKFLOW"] = "WORKFLOW"
    event_name: Literal["COMPLETED"] = "COMPLETED"

    run_id: str
    """The ID of the workflow"""
    workflow_name: str
    """The name of the workflow"""

    @classmethod
    def from_wf_run(cls, wf_run: WorkflowRun) -> "WorkflowCompletedEvent":
        """Create a new workflow completed event"""
        return WorkflowCompletedEvent(
            experiment_id=wf_run.experiment_id,
            run_id=wf_run.run_id,
            workflow_name=wf_run.name,
        )


class WorkflowCancelled(Event):
    """Event for a workflow being cancelled"""

    event_type: Literal["WORKFLOW"] = "WORKFLOW"
    event_name: Literal["CANCELLED"] = "CANCELLED"

    run_id: str
    """The ID of the workflow"""
    workflow_name: str
    """The name of the workflow"""

    @classmethod
    def from_wf_run(cls, wf_run: WorkflowRun) -> "WorkflowCancelled":
        """Create a new workflow cancelled event"""
        return WorkflowCancelled(
            experiment_id=wf_run.experiment_id,
            run_id=wf_run.run_id,
            workflow_name=wf_run.name,
        )


class WorkflowPausedEvent(Event):
    """Event for a workflow being paused"""

    event_type: Literal["WORKFLOW"] = "WORKFLOW"
    event_name: Literal["PAUSED"] = "PAUSED"

    run_id: str
    """The ID of the workflow"""
    workflow_name: str
    """The name of the workflow"""

    @classmethod
    def from_wf_run(cls, wf_run: WorkflowRun) -> "WorkflowPausedEvent":
        """Create a new workflow paused event"""
        return WorkflowPausedEvent(
            experiment_id=wf_run.experiment_id,
            run_id=wf_run.run_id,
            workflow_name=wf_run.name,
        )


class WorkflowResumedEvent(Event):
    """Event for a workflow being resumed"""

    event_type: Literal["WORKFLOW"] = "WORKFLOW"
    event_name: Literal["RESUMED"] = "RESUMED"

    run_id: str
    """The ID of the workflow"""
    workflow_name: str
    """The name of the workflow"""

    @classmethod
    def from_wf_run(cls, wf_run: WorkflowRun) -> "WorkflowResumedEvent":
        """Create a new workflow resumed event"""
        return WorkflowResumedEvent(
            experiment_id=wf_run.experiment_id,
            run_id=wf_run.run_id,
            workflow_name=wf_run.wf_name,
        )


class WorkflowStepEvent(Event):
    """Event for a workflow step"""

    event_type: Literal["WORKFLOW"] = "WORKFLOW"
    event_name: Literal["STEP"] = "STEP"

    run_id: str
    """The ID of the workflow"""
    workflow_name: str
    """The name of the workflow"""
    step_index: int
    """The index of the step"""
    step: Step
    """The step"""

    @classmethod
    def from_wf_run(cls, wf_run: WorkflowRun, step: Step) -> "WorkflowStepEvent":
        """Create a new workflow step event"""
        return WorkflowStepEvent(
            experiment_id=wf_run.experiment_id,
            run_id=wf_run.run_id,
            workflow_name=wf_run.name,
            step_index=wf_run.step_index,
            step=step,
        )
