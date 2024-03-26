"""Types related to Events"""

from typing import Any, Dict, List, Literal, Optional

from wei.types.base_types import BaseModel
from wei.types.experiment_types import Campaign, ExperimentDataPoint, ExperimentInfo
from wei.types.step_types import Step
from wei.types.workflow_types import WorkflowRun


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
    event_info: Campaign

    @classmethod
    def new_event(cls, campaign: Campaign) -> "CreateCampaignEvent":
        """Create a new create campaign event"""
        return CreateCampaignEvent(event_info=campaign)


class ExperimentStartEvent(Event):
    """Event for starting an experiment"""

    event_type: Literal["EXPERIMENT"] = "EXPERIMENT"
    event_name: Literal["START"] = "START"
    event_info: ExperimentInfo

    @classmethod
    def new_event(cls, experiment_info: ExperimentInfo) -> "ExperimentStartEvent":
        """Create a new start experiment event"""
        return ExperimentStartEvent(event_info=experiment_info)


class ExperimentContinueEvent(Event):
    """Event for continuing an experiment"""

    event_type: Literal["EXPERIMENT"] = "EXPERIMENT"
    event_name: Literal["CONTINUE"] = "CONTINUE"
    event_info: Optional[ExperimentInfo] = None

    @classmethod
    def new_event(
        cls,
        experiment_info: Optional[ExperimentInfo] = None,
    ) -> "ExperimentContinueEvent":
        """Create a new continue experiment event"""
        return ExperimentContinueEvent(event_info=experiment_info)


class ExperimentEndEvent(Event):
    """Event for ending an experiment"""

    event_type: Literal["EXPERIMENT"] = "EXPERIMENT"
    event_name: Literal["END"] = "END"
    event_info: Optional[ExperimentInfo] = None

    @classmethod
    def new_event(
        cls,
        experiment_info: Optional[ExperimentInfo] = None,
    ) -> "ExperimentEndEvent":
        """Create a new end experiment event"""
        return ExperimentEndEvent(event_info=experiment_info)


class ExperimentDataPointEvent(Event):
    """Event for a data point in an experiment"""

    event_type: Literal["EXPERIMENT"] = "EXPERIMENT"
    event_name: Literal["DATA_POINT"] = "DATA_POINT"
    event_info: ExperimentDataPoint

    @classmethod
    def new_event(cls, data_point: ExperimentDataPoint) -> "ExperimentDataPointEvent":
        """Create a new data point event"""
        return ExperimentDataPointEvent(event_info=data_point)


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

    @classmethod
    def new_event(
        cls, decision_name: str, decision_value: Optional[str] = None
    ) -> "DecisionEvent":
        """Create a new decision event"""
        return DecisionEvent(
            event_info=DecisionEvent.DecisionEventInfo(
                decision_name=decision_name,
                decision_value=decision_value,
            ),
        )


class CommentEvent(Event):
    """Event for a comment"""

    class CommentEventInfo(BaseModel):
        """Information about the comment event"""

        comment: str
        """The comment"""

    event_type: Literal["EXPERIMENT"] = "EXPERIMENT"
    event_name: Literal["COMMENT"] = "COMMENT"
    event_info: CommentEventInfo

    @classmethod
    def new_event(cls, comment: str) -> "CommentEvent":
        """Create a new comment event"""
        return CommentEvent(event_info=CommentEvent.CommentEventInfo(comment=comment))


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

    @classmethod
    def new_event(
        cls,
        function_name: str,
        args: Optional[List[Any]] = None,
        kwargs: Optional[Dict[str, Any]] = None,
        result: Optional[Any] = None,
    ) -> "LocalComputeEvent":
        """Create a new local compute event"""
        return LocalComputeEvent(
            event_info=LocalComputeEvent.LocalComputeEventInfo(
                function_name=function_name,
                args=args,
                kwargs=kwargs,
                result=result,
            ),
        )


class GlobusComputeEvent(Event):
    """Event for a globus computation"""

    class GlobusComputeEventInfo(BaseModel):
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
    event_info: GlobusComputeEventInfo

    @classmethod
    def new_event(
        cls,
        function_name: str,
        args: Optional[List[Any]] = None,
        kwargs: Optional[Dict[str, Any]] = None,
        result: Optional[Any] = None,
    ) -> "GlobusComputeEvent":
        """Create a new globus compute event"""
        return GlobusComputeEvent(
            event_info=GlobusComputeEvent.GlobusComputeEventInfo(
                function_name=function_name,
                args=args,
                kwargs=kwargs,
                result=result,
            ),
        )


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

    @classmethod
    def new_event(cls, flow_name: str, flow_id: str) -> "GladierFlowEvent":
        """Create a new Gladier Flow event"""
        return GladierFlowEvent(
            event_info=GladierFlowEvent.GladierFlowEventInfo(
                flow_name=flow_name,
                flow_id=flow_id,
            ),
        )


class LoopStartEvent(Event):
    """Event for the start of a loop"""

    class LoopStartEventInfo(BaseModel):
        """Information about the loop start event"""

        loop_name: str
        """The name of the loop"""

    event_type: Literal["EXPERIMENT"] = "EXPERIMENT"
    event_name: Literal["LOOP_START"] = "LOOP_START"
    event_info: LoopStartEventInfo

    @classmethod
    def new_event(cls, loop_name: str) -> "LoopStartEvent":
        """Create a new loop start event"""
        return LoopStartEvent(
            event_info=LoopStartEvent.LoopStartEventInfo(loop_name=loop_name)
        )


class LoopEndEvent(Event):
    """Event for the end of a loop"""

    class LoopEndEventInfo(BaseModel):
        """Information about the loop end event"""

        loop_name: str
        """The name of the loop"""

    event_type: Literal["EXPERIMENT"] = "EXPERIMENT"
    event_name: Literal["LOOP_END"] = "LOOP_END"
    event_info: LoopEndEventInfo

    @classmethod
    def new_event(cls, loop_name: str) -> "LoopEndEvent":
        """Create a new loop end event"""
        return LoopEndEvent(
            event_info=LoopEndEvent.LoopEndEventInfo(loop_name=loop_name)
        )


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

    @classmethod
    def new_event(
        cls, loop_name: str, conditional: str, result: bool
    ) -> "LoopCheckEvent":
        """Create a new loop check event"""
        return LoopCheckEvent(
            event_info=LoopCheckEvent.LoopCheckEventInfo(
                loop_name=loop_name,
                conditional=conditional,
                result=result,
            ),
        )


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

    @classmethod
    def new_event(cls, wf_run: WorkflowRun) -> "WorkflowQueuedEvent":
        """Create a new workflow queued event"""
        return WorkflowQueuedEvent(
            experiment_id=wf_run.experiment_id,
            event_info=WorkflowQueuedEvent.WorkflowQueuedEventInfo(
                run_id=wf_run.run_id,
                workflow_name=wf_run.name,
            ),
        )


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

    @classmethod
    def new_event(cls, wf_run: WorkflowRun) -> "WorkflowStartEvent":
        """Create a new workflow start event"""
        return WorkflowStartEvent(
            experiment_id=wf_run.experiment_id,
            event_info=WorkflowStartEvent.WorkflowStartEventInfo(
                run_id=wf_run.run_id,
                workflow_name=wf_run.name,
            ),
        )


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

    @classmethod
    def new_event(cls, wf_run: WorkflowRun) -> "WorkflowFailedEvent":
        """Create a new workflow failed event"""
        return WorkflowFailedEvent(
            experiment_id=wf_run.experiment_id,
            event_info=WorkflowFailedEvent.WorkflowFailedEventInfo(
                run_id=wf_run.run_id,
                workflow_name=wf_run.name,
            ),
        )


class WorkflowCompletedEvent(Event):
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

    @classmethod
    def new_event(cls, wf_run: WorkflowRun) -> "WorkflowCompletedEvent":
        """Create a new workflow completed event"""
        return WorkflowCompletedEvent(
            experiment_id=wf_run.experiment_id,
            event_info=WorkflowCompletedEvent.WorkflowCompletedEventInfo(
                run_id=wf_run.run_id,
                workflow_name=wf_run.name,
            ),
        )


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

    @classmethod
    def new_event(cls, wf_run: WorkflowRun) -> "WorkflowCancelled":
        """Create a new workflow cancelled event"""
        return WorkflowCancelled(
            experiment_id=wf_run.experiment_id,
            event_info=WorkflowCancelled.WorkflowCancelledEventInfo(
                run_id=wf_run.run_id,
                workflow_name=wf_run.name,
            ),
        )


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

    @classmethod
    def new_event(cls, wf_run: WorkflowRun) -> "WorkflowPausedEvent":
        """Create a new workflow paused event"""
        return WorkflowPausedEvent(
            experiment_id=wf_run.experiment_id,
            event_info=WorkflowPausedEvent.WorkflowPausedEventInfo(
                run_id=wf_run.run_id,
                workflow_name=wf_run.name,
            ),
        )


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

    @classmethod
    def new_event(cls, wf_run: WorkflowRun) -> "WorkflowResumedEvent":
        """Create a new workflow resumed event"""
        return WorkflowResumedEvent(
            experiment_id=wf_run.experiment_id,
            event_info=WorkflowResumedEvent.WorkflowResumedEventInfo(
                run_id=wf_run.run_id,
                workflow_name=wf_run.wf_name,
            ),
        )


class WorkflowStepEvent(Event):
    """Event for a workflow step"""

    class WorkflowStepEventInfo(BaseModel):
        """Information about the workflow step"""

        run_id: str
        """The ID of the workflow"""
        workflow_name: str
        """The name of the workflow"""
        step_index: int
        """The index of the step"""
        step: Step
        """The step"""

    event_type: Literal["WORKFLOW"] = "WORKFLOW"
    event_name: Literal["STEP"] = "STEP"
    event_info: WorkflowStepEventInfo

    @classmethod
    def new_event(cls, wf_run: WorkflowRun, step: Step) -> "WorkflowStepEvent":
        """Create a new workflow step event"""
        return WorkflowStepEvent(
            experiment_id=wf_run.experiment_id,
            event_info=WorkflowStepEvent.WorkflowStepEventInfo(
                run_id=wf_run.run_id,
                workflow_name=wf_run.name,
                step_index=wf_run.step_index,
                step=step,
            ),
        )
