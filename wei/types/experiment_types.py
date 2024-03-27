"""Types related to experiments"""

from typing import Any, Dict, List, Optional

from pydantic import AliasChoices, Field

from wei.types.base_types import BaseModel, ulid_factory


class Campaign(BaseModel):
    """A campaign is a collection of related experiments"""

    campaign_name: str
    """Name of the campaign"""
    campaign_id: str = Field(default_factory=ulid_factory)
    """ID of the campaign"""
    experiment_ids: List[str] = []
    """Experiments associated with the campaign"""


class ExperimentDataPoint(BaseModel):
    """A single data point from an experiment"""

    experiment_id: str
    """The ID of the experiment"""
    params: Dict[str, Any] = {}
    """Parameters for the experiment that generated the data point"""
    outputs: Dict[str, Any] = {}
    """Experimental Outputs"""


class ExperimentDataField(BaseModel):
    """Defines a single field in the data"""

    type: str
    """Type of the field"""
    description: Optional[str] = None
    """Description of the field"""
    example: Optional[Any] = None
    """An example value for the field"""


class ExperimentDesign(BaseModel):
    """Definition for an experiment"""

    experiment_name: Optional[str] = Field(
        default=None, alias=AliasChoices("name", "experiment_name")
    )
    """Name of the experiment"""
    campaign_id: Optional[str] = None
    """ID of the campaign this experiment should be associated with (note: this campaign must already exist)"""
    description: Optional[str] = None
    """Description of the experiment"""
    parameters: Optional[Dict[str, ExperimentDataField]] = None
    """Parameters for the experiment"""
    outputs: Optional[Dict[str, ExperimentDataField]] = None
    """Outputs from a single iteration of the experiment's loop"""


class Experiment(ExperimentDesign):
    """Definition and metadata for an experiment"""

    experiment_id: str = Field(default_factory=ulid_factory)
    """ID of the experiment"""
