"""Types related to experiments"""

from typing import Any, List, Optional

from pydantic import (
    Field,
)

from wei.types.base_types import BaseModel, ulid_factory


class DataPoint(BaseModel):
    """Generic experiment data point type"""

    experiment_id: str
    """ID of the experiment this data point belongs to"""
    campaign_id: Optional[str] = None
    """ID of the campaign this data point belongs to"""
    data_point_id: str = Field(default_factory=ulid_factory)
    """ID of the data point"""
    input: Any
    """Input data for the data point"""
    output: Any
    """Output data for the data point"""


class Campaign(BaseModel):
    """A campaign is a collection of related experiments"""

    campaign_name: str
    """Name of the campaign"""
    campaign_id: str = Field(default_factory=ulid_factory)
    """ID of the campaign"""
    experiments: List[str] = []
    """Experiments associated with the campaign"""


class ExperimentDataClass(BaseModel):
    """Definition for an experiment"""

    experiment_id: Optional[str] = Field(default_factory=ulid_factory)
    """ID of the experiment"""
    experiment_name: Optional[str]  # = Field(default_factory=get_experiment_name)
    """Name of the experiment"""
    campaign_id: Optional[str] = None
    """ID of the campaign this experiment is associated with"""
    data_points: List[DataPoint] = []
    """Data points associated with the experiment"""
