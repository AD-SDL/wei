"""Types related to experiments"""

from typing import Dict, List, Optional

from pydantic import (
    Field,
)

from wei.types.base_types import BaseModel, ulid_factory


class Campaign(BaseModel):
    """A campaign is a collection of related experiments"""

    campaign_name: str
    """Name of the campaign"""
    campaign_id: str = Field(default_factory=ulid_factory)
    """ID of the campaign"""
    experiment_ids: List[str] = []
    """Experiments associated with the campaign"""


class ExperimentDataField(BaseModel):
    """Defines a single field in the data"""

    type: str
    """Type of the field"""
    description: Optional[str] = None
    """Description of the field"""


class ExperimentDesign(BaseModel):
    """Definition for an experiment"""

    experiment_name: Optional[str] = None
    """Name of the experiment"""
    campaign_id: Optional[str] = None
    """ID of the campaign this experiment should be associated with (note: this campaign must already exist)"""
    inputs: Optional[Dict[str, ExperimentDataField]] = None
    """Inputs to a single iteration of the experiment's loop"""
    outputs: Optional[Dict[str, ExperimentDataField]] = None
    """Outputs from a single iteration of the experiment's loop"""


class ExperimentInfo(ExperimentDesign):
    """Definition and metadata for an experiment"""

    experiment_id: str = Field(default_factory=ulid_factory)
    """ID of the experiment"""
