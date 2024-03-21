"""
Router for the "events" endpoints
"""

import threading
from typing import Any

from fastapi import APIRouter

from wei.core.loggers.event_logger import EventLogger
from wei.types import Event

router = APIRouter()


@router.post("/")
def log_event(event: Event) -> Any:
    """Logs a value to the log file for a given experiment"""
    thread = threading.Thread(target=EventLogger(event.experiment_id).log_event(event))
    thread.start()

    return event
