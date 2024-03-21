"""
Router for the "events" endpoints
"""

from typing import Any

from fastapi import APIRouter

from wei.core.logs.event_logger import EventLogger
from wei.types import Event

router = APIRouter()


@router.post("/")
def log_event(event: Event) -> Any:
    """Logs a value to the log file for a given experiment"""
    EventLogger(event.experiment_id).log_event(event)
    return event
