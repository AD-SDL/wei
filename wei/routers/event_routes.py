"""
Router for the "events" endpoints
"""

import threading
from typing import Any

from fastapi import APIRouter

from wei.core.events import EventHandler
from wei.types import Event

router = APIRouter()


@router.post("/")
def log_event(event: Event) -> Any:
    """Logs a value to the log file for a given experiment"""
    thread = threading.Thread(target=EventHandler.log_event(event))
    thread.start()

    return event
