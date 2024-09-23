"""Types related to experiments"""

from datetime import datetime
from typing import List, Optional

from pydantic import AliasChoices, Field

from wei.types.base_types import BaseModel, PathLike, ulid_factory


class CampaignDesign(BaseModel):
    """Design of a campaign"""

    campaign_name: str
    """Name of the campaign"""
    campaign_description: Optional[str] = None
    """Description of the campaign"""


class Campaign(CampaignDesign):
    """A campaign is a collection of related experiments"""

    campaign_id: str = Field(default_factory=ulid_factory)
    """ID of the campaign"""
    experiment_ids: List[str] = []
    """Experiments associated with the campaign"""


class ExperimentDesign(BaseModel):
    """Design of an experiment"""

    experiment_name: str = Field(alias=AliasChoices("name", "experiment_name"))
    """Name of the experiment"""
    campaign_id: Optional[str] = None
    """ID of the campaign this experiment should be associated with (note: this campaign must already exist)"""
    experiment_description: Optional[str] = None
    """Description of the experiment"""
    email_addresses: List[str] = []
    """List of email addresses to send notifications to"""


class Experiment(ExperimentDesign):
    """A single instance of an experiment"""

    experiment_id: str = Field(default_factory=ulid_factory)
    """ID of the experiment"""
    experiment_directory: Optional[PathLike] = None
    """The directory where the experiment is stored on disk"""
    check_in_timestamp: Optional[datetime] = None
    """The last time the experiment client checked in"""
