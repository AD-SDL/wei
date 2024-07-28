"""Types related to datapoint types"""

from typing import Any, Literal, Optional

from pydantic import Field

from wei.types.base_types import BaseModel, ulid_factory


class DataPoint(BaseModel, extra="allow"):
    """An object to contain and locate data identified by modules"""

    label: str
    """label of this data point"""
    step_id: Optional[str]
    """step that generated the data point"""
    workflow_id: Optional[str]
    """workflow that generated the data point"""
    experiment_id: Optional[str]
    """experiment that generated the data point"""
    type: str
    """type of the datapoint, inherited from class"""
    campaign_id: Optional[str] = None
    """campaign of the data point"""
    id: str = Field(default_factory=ulid_factory)
    """specific id for this data point"""


class LocalFileDataPoint(DataPoint):
    """a datapoint containing a file"""

    type: Literal["local_file"] = "local_file"
    """local file"""
    path: str
    """path to the file"""


class ValueDataPoint(DataPoint):
    """a datapoint contained in the Json value"""

    type: Literal["data_value"] = "data_value"
    """data_value"""
    value: Any
    """value of the data point"""
