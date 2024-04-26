"""
Router for the "events" endpoints
"""

import threading
from typing import Any

from fastapi import APIRouter

from wei.core.events import EventHandler
from wei.core.state_manager import StateManager
from wei.types import Event

router = APIRouter()

state_manager = StateManager()


@router.post("/")
def log_event(event: Event) -> Any:
    """Logs a value to the log file for a given experiment"""
    thread = threading.Thread(target=EventHandler.log_event(event))
    thread.start()

    return event


@router.get("/{event_id}")
def get_event(event_id: str) -> Event:
    """Returns the details for a specific event given the id"""
    return state_manager.get_event(event_id)


@router.get("/")
def get_all_events(event_id: str) -> Event:
    """Returns the details for a specific event given the id"""
    return state_manager.get_all_events()
