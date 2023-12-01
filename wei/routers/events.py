"""
Router for the "events" endpoints
"""

from typing import Any
from fastapi import APIRouter
from wei.core.events import EventLogger, Event

router = APIRouter()

@router.post("/")
def log_event(event: Any) -> Any:
    """Logs a value to the log file for a given experiment"""
    print(event)
    EventLogger(event.experiment_id).log_event(event)
    return event
