"""Types related to Events"""

from typing import Any, Dict, List, Literal, Optional

from wei.types.base_types import BaseModel


class Event(BaseModel):
    """A single event in an experiment"""

    experiment_id: Optional[str] = None
    campaign_id: Optional[str] = None
    workcell_id: Optional[str] = None
    event_type: str
    event_name: str
    event_info: Optional[Any] = None


class CreateCampaignEvent(Event):
    """Event for creating a campaign"""

    event_type: Literal["CAMPAIGN"] = "CAMPAIGN"
    event_name: Literal["CREATE"] = "CREATE"


class ExperimentStartEvent(Event):
    """Event for starting an experiment"""

    event_type: Literal["EXPERIMENT"] = "EXPERIMENT"
    event_name: Literal["START"] = "CONTINUE"


class ExperimentContinueEvent(Event):
    """Event for continuing an experiment"""

    event_type: Literal["EXPERIMENT"] = "EXPERIMENT"
    event_name: Literal["CONTINUE"] = "CONTINUE"


class ExperimentEndEvent(Event):
    """Event for ending an experiment"""

    event_type: Literal["EXPERIMENT"] = "EXPERIMENT"
    event_name: Literal["END"] = "END"


class DecisionEvent(Event):
    """Event for a decision"""

    class DecisionEventInfo(BaseModel):
        """Information about the decision event"""

        decision_name: str
        """The decision made"""

        decision_value: Optional[str] = None
        """The reason for the decision"""

    event_type: Literal["EXPERIMENT"] = "EXPERIMENT"
    event_name: Literal["DECISION"] = "DECISION"
    event_info: DecisionEventInfo


class CommentEvent(Event):
    """Event for a comment"""

    class CommentEventInfo(BaseModel):
        """Information about the comment event"""

        comment: str
        """The comment"""

    event_type: Literal["EXPERIMENT"] = "EXPERIMENT"
    event_name: Literal["COMMENT"] = "COMMENT"
    event_info: CommentEventInfo


class LocalComputeEvent(Event):
    """Event for a local computation"""

    class LocalComputeEventInfo(BaseModel):
        """Information about the local computation event"""

        function_name: str
        """The name of the function called"""
        args: Optional[List[Any]] = None
        """The positional args passed to the function"""
        kwargs: Optional[Dict[str, Any]] = None
        """The keyword args passed to the function"""
        result: Optional[Any] = None
        """The result of the computation"""

    event_type: Literal["EXPERIMENT"] = "EXPERIMENT"
    event_name: Literal["LOCAL_COMPUTE"] = "LOCAL_COMPUTE"
    event_info: LocalComputeEventInfo


class GlobusComputeEvent(Event):
    """Event for a globus computation"""

    class LocalComputeEventInfo(BaseModel):
        """Information about the local computation event"""

        function_name: str
        """The name of the function called"""
        args: Optional[List[Any]] = None
        """The positional args passed to the function"""
        kwargs: Optional[Dict[str, Any]] = None
        """The keyword args passed to the function"""
        result: Optional[Any] = None
        """The result of the computation"""

    event_type: Literal["EXPERIMENT"] = "EXPERIMENT"
    event_name: Literal["GLOBUS_COMPUTE"] = "GLOBUS_COMPUTE"
    event_info: LocalComputeEventInfo


class GladierFlowEvent(Event):
    """Event for a Gladier Flow"""

    class GladierFlowEventInfo(BaseModel):
        """Information about the Gladier Flow event"""

        flow_name: str
        """The name of the flow"""
        flow_id: str
        """The ID of the flow"""

    event_type: Literal["EXPERIMENT"] = "EXPERIMENT"
    event_name: Literal["GLADIER_FLOW"] = "GLADIER_FLOW"
    event_info: GladierFlowEventInfo


class LoopStartEvent(Event):
    """Event for the start of a loop"""

    class LoopStartEventInfo(BaseModel):
        """Information about the loop start event"""

        loop_name: str
        """The name of the loop"""

    event_type: Literal["EXPERIMENT"] = "EXPERIMENT"
    event_name: Literal["LOOP_START"] = "LOOP_START"
    event_info: LoopStartEventInfo


class LoopEndEvent(Event):
    """Event for the end of a loop"""

    class LoopEndEventInfo(BaseModel):
        """Information about the loop end event"""

        loop_name: str
        """The name of the loop"""

    event_type: Literal["EXPERIMENT"] = "EXPERIMENT"
    event_name: Literal["LOOP_END"] = "LOOP_END"
    event_info: LoopEndEventInfo


class LoopCheckEvent(Event):
    """Event for the conditional check of a loop"""

    class LoopCheckEventInfo(BaseModel):
        """Information about the loop end event"""

        loop_name: str
        """The name of the loop"""
        conditional: str
        """The conditional that was checked"""
        result: bool

    event_type: Literal["EXPERIMENT"] = "EXPERIMENT"
    event_name: Literal["LOOP_CHECK"] = "LOOP_CHECK"
    event_info: LoopCheckEventInfo


class WorkflowQueuedEvent(Event):
    """Event for a workflow being queued"""

    class WorkflowQueuedEventInfo(BaseModel):
        """Information about the workflow being queued"""

        run_id: str
        """The ID of the workflow"""
        workflow_name: str
        """The name of the workflow"""

    event_type: Literal["WORKFLOW"] = "WORKFLOW"
    event_name: Literal["QUEUED"] = "QUEUED"
    event_info: WorkflowQueuedEventInfo


class WorkflowStartEvent(Event):
    """Event for a workflow starting"""

    class WorkflowStartEventInfo(BaseModel):
        """Information about the workflow starting"""

        run_id: str
        """The ID of the workflow"""
        workflow_name: str
        """The name of the workflow"""

    event_type: Literal["WORKFLOW"] = "WORKFLOW"
    event_name: Literal["START"] = "START"
    event_info: WorkflowStartEventInfo


class WorkflowFailedEvent(Event):
    """Event for a workflow failing"""

    class WorkflowFailedEventInfo(BaseModel):
        """Information about the workflow failing"""

        run_id: str
        """The ID of the workflow"""
        workflow_name: str
        """The name of the workflow"""

    event_type: Literal["WORKFLOW"] = "WORKFLOW"
    event_name: Literal["FAILED"] = "FAILED"
    event_info: WorkflowFailedEventInfo


class WorkflowCompleted(Event):
    """Event for a workflow completing"""

    class WorkflowCompletedEventInfo(BaseModel):
        """Information about the workflow completing"""

        run_id: str
        """The ID of the workflow"""
        workflow_name: str
        """The name of the workflow"""

    event_type: Literal["WORKFLOW"] = "WORKFLOW"
    event_name: Literal["COMPLETED"] = "COMPLETED"
    event_info: WorkflowCompletedEventInfo


class WorkflowCancelled(Event):
    """Event for a workflow being cancelled"""

    class WorkflowCancelledEventInfo(BaseModel):
        """Information about the workflow being cancelled"""

        run_id: str
        """The ID of the workflow"""
        workflow_name: str
        """The name of the workflow"""

    event_type: Literal["WORKFLOW"] = "WORKFLOW"
    event_name: Literal["CANCELLED"] = "CANCELLED"
    event_info: WorkflowCancelledEventInfo


class WorkflowPausedEvent(Event):
    """Event for a workflow being paused"""

    class WorkflowPausedEventInfo(BaseModel):
        """Information about the workflow being paused"""

        run_id: str
        """The ID of the workflow"""
        workflow_name: str
        """The name of the workflow"""

    event_type: Literal["WORKFLOW"] = "WORKFLOW"
    event_name: Literal["PAUSED"] = "PAUSED"
    event_info: WorkflowPausedEventInfo


class WorkflowResumedEvent(Event):
    """Event for a workflow being resumed"""

    class WorkflowResumedEventInfo(BaseModel):
        """Information about the workflow being resumed"""

        run_id: str
        """The ID of the workflow"""
        workflow_name: str
        """The name of the workflow"""

    event_type: Literal["WORKFLOW"] = "WORKFLOW"
    event_name: Literal["RESUMED"] = "RESUMED"
    event_info: WorkflowResumedEventInfo
