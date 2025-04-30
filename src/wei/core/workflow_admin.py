"""Shared workflow admin module. Creates thread used for handling workflow admin commands."""

import threading

wf_status_change = threading.Event()
