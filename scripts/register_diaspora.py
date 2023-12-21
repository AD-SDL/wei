#!/usr/bin/env python
"""Pre-register Diaspora so we don't have to wait for it to be ready on first run."""

from diaspora_event_sdk import Client, block_until_ready

Client()
print("Validating diaspora is ready, this might take 1-2 minutes...")
if block_until_ready():
    print("Diaspora is ready!")
else:
    print("Diaspora is not ready yet, please try again in a few minutes.")
