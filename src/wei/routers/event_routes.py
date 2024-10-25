"""
Router for the "events" endpoints
"""

from typing import Any, Dict

from fastapi import APIRouter

from wei.core.events import EventHandler
from wei.core.state_manager import state_manager
from wei.types import Event

router = APIRouter()


@router.post("/")
def log_event(event: Event) -> Any:
    """Logs a value to the log file for a given experiment"""
    EventHandler.log_event(event)

    return event


@router.get("/")
@router.get("/all")
def get_all_events() -> Dict[str, Event]:
    """Returns all events stored in the event cache."""
    return state_manager.get_all_events()


@router.get("/{event_id}")
def get_event(event_id: str) -> Event:
    """Returns the details for a specific event given the id"""
    return state_manager.get_event(event_id)
