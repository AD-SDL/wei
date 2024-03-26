"""Contains the Events class for logging experiment steps"""

from typing import Any

import requests

from wei.config import Config
from wei.types import Event


def log_event(event: Event) -> Any:
    """Logs an event to the server"""

    event.workcell_id = getattr(Config, "workcell_id", None)
    url = f"http://{Config.server_host}:{Config.server_port}/events/"
    response = requests.post(
        url,
        json=event.model_dump(mode="json"),
    )
    if response.ok:
        return response.json()
    else:
        response.raise_for_status()
