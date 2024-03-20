"""Types related to Events"""

from typing import Any, Optional

from wei.types.base_types import BaseModel


class Event(BaseModel):
    """A single event in an experiment"""

    experiment_id: str
    workcell_id: Optional[str] = None
    event_type: str
    event_name: str
    event_info: Optional[Any] = None
