"""Types related to Events"""

from typing import Any, Optional

from wei.types.base_types import BaseModel


class Event(BaseModel):
    """A single event in an experiment"""

    experiment_id: str
    campaign_id: Optional[str] = None
    workcell_id: Optional[str] = None
    event_type: str
    event_name: str
    event_info: Optional[Any] = None


# class EventCategory(str, Enum):
#     """Categories for events"""

#     CAMPAIGN = "CAMPAIGN"
#     EXPERIMENT = "EXPERIMENT"
#     WORKCELL = "WORKCELL"
#     WORKFLOW = "WORKFLOW"
#     STEP = "STEP"


# class Event(BaseModel):
#     """A single event in an experiment"""

#     experiment_id: str
#     campaign_id: Optional[str] = None
#     workcell_id: Optional[str] = None
#     event_category: str
#     event_name: str
#     event_info: Optional[Any] = None

#     @classmethod
#     def create_event(
#         cls: "Event",
#         experiment_id: str,
#         event_category: EventCategory,
#         event_name: str,
#         campaign_id: Optional[str] = None,
#         event_info: Optional[Any] = None,
#     ) -> "Event":
#         """Create a new event."""
#         return cls(
#             experiment_id=experiment_id,
#             campaign_id=campaign_id,
#             event_category=event_category,
#             event_name=event_name,
#             event_info=event_info,
#         )


# ################################################################################


# class CampaignEventNames(str, Enum):
#     """Names for campaign events"""

#     CREATE = "CREATE"


# class CampaignEvent(Event):
#     """A campaign level event."""

#     event_category: Literal[EventCategory.CAMPAIGN]
#     event_name: CampaignEventNames


# class CreateCampaignEvent(CampaignEvent):
#     """A campaign was started."""

#     event_name: Literal[CampaignEventNames.CREATE] = CampaignEventNames.CREATE
#     event_info: None

#     @classmethod
#     def create_event(
#         cls: "CreateCampaignEvent",
#         experiment_id: str,
#         campaign_id: str,
#     ) -> Event:
#         """Create a new create campaign event."""
#         return super.create_event(
#             experiment_id=experiment_id,
#             campaign_id=campaign_id,
#             event_category=EventCategory.CAMPAIGN,
#             event_name=cls.event_name,
#             event_info=None,
#         )


# ################################################################################


# class ExperimentEventNames(str, Enum):
#     """Names for experiment events"""

#     START = "START"
#     RESUME = "RESUME"
#     END = "END"
#     DECISION = "DECISION"
#     DATA_POINT = "DATA_POINT"
#     COMMENT = "COMMENT"
#     COMPUTE = "COMPUTE"
#     LOOP_START = "LOOP_START"
#     LOOP_END = "LOOP_END"
#     LOOP_CHECK = "LOOP_CHECK"
#     LOCAL_COMPUTE = "LOCAL_COMPUTE"
#     GLOBUS_COMPUTE = "GLOBUS_COMPUTE"
#     GLOBUS_TRANSFER = "GLOBUS_TRANSFER"


# class ExperimentEvent(Event):
#     """An experiment level event."""

#     event_category: Literal[EventCategory.EXPERIMENT]
#     event_name: ExperimentEventNames

#     @classmethod
#     def create_event(
#         cls: "ExperimentEvent",
#         experiment_id: str,
#         event_name: str,
#         campaign_id: Optional[str] = None,
#         event_info: Optional[Any] = None,
#     ) -> "ExperimentEvent":
#         """Create a new start experiment event."""
#         return super.create_event(
#             experiment_id=experiment_id,
#             campaign_id=campaign_id,
#             event_category=EventCategory.EXPERIMENT,
#             event_name=event_name,
#             event_info=event_info,
#         )


# class StartExperimentEvent(ExperimentEvent):
#     """An experiment was started."""

#     event_name: Literal[ExperimentEventNames.START] = ExperimentEventNames.START
#     event_info: None

#     @classmethod
#     def create_event(
#         cls: "StartExperimentEvent",
#         experiment_id: str,
#         campaign_id: Optional[str] = None,
#     ) -> Event:
#         """Create a new start experiment event."""
#         return super.create_event(
#             experiment_id=experiment_id,
#             campaign_id=campaign_id,
#             event_category=EventCategory.EXPERIMENT,
#             event_name=cls.event_name,
#             event_info=None,
#         )


# class ResumeExperimentEvent(ExperimentEvent):
#     """An experiment was resumed."""

#     event_name: Literal[ExperimentEventNames.RESUME]
#     event_info: None

#     @classmethod
#     def create_event(
#         cls: "ResumeExperimentEvent",
#         experiment_id: str,
#         campaign_id: Optional[str] = None,
#     ) -> Event:
#         """Create a new start experiment event."""
#         return super.create_event(
#             experiment_id=experiment_id,
#             campaign_id=campaign_id,
#             event_category=EventCategory.EXPERIMENT,
#             event_name=cls.event_name,
#             event_info=None,
#         )


# class EndExperimentEvent(ExperimentEvent):
#     """An experiment ended."""

#     event_name: Literal[ExperimentEventNames.START]
#     event_info: None

#     @classmethod
#     def create_event(
#         cls: "StartExperimentEvent",
#         experiment_id: str,
#         campaign_id: Optional[str] = None,
#     ) -> "StartExperimentEvent":
#         """Create a new start experiment event."""
#         return super.create_event(
#             experiment_id=experiment_id,
#             campaign_id=campaign_id,
#             event_category=EventCategory.EXPERIMENT,
#             event_name=cls.event_name,
#             event_info=None,
#         )


# ################################################################################


# class WorkcellEvent(Event):
#     """A workcell level event."""

#     class WorkcellEventNames(str, Enum):
#         """Names for workcell events"""

#         START = "START"
#         ESTOP = "ESTOP"
#         PAUSE = "PAUSE"
#         RESUME = "RESUME"
#         SHUTDOWN = "SHUTDOWN"

#     event_category: Literal[EventCategory.WORKCELL]
#     event_name: WorkcellEventNames


# ################################################################################


# class WorkflowEvent(Event):
#     """A workflow level event."""

#     class WorkflowEventNames(str, Enum):
#         """Names for workflow events"""

#         QUEUED = "QUEUED"
#         START = "START"
#         END = "END"
#         PAUSE = "PAUSE"
#         RESUME = "RESUME"
#         CANCEL = "CANCEL"
#         FAILED = "FAILED"
#         ESTOP = "ESTOP"

#     event_category: Literal[EventCategory.WORKFLOW]
#     event_name: WorkflowEventNames


# ################################################################################
# class StepEvent(Event):
#     """A step level event."""

#     class StepEventNames(str, Enum):
#         """Names for step events"""

#         START = "START"
#         SUCCEEDED = "SUCCEEDED"
#         FAILED = "FAILED"
#         PAUSE = "PAUSE"
#         RESUME = "RESUME"
#         CANCEL = "CANCEL"
#         ESTOP = "ESTOP"

#     event_category: Literal[EventCategory.STEP]
#     event_name: StepEventNames
