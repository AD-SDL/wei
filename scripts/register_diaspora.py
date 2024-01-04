#!/usr/bin/env python
"""Pre-register Diaspora so we don't have to wait for it to be ready on first run."""

from pathlib import Path

from diaspora_event_sdk import Client, block_until_ready


def remove_files_and_directories(directory_path):
    """Remove all files and directories in a given directory."""
    directory = Path(directory_path).expanduser().resolve()

    if not directory.is_dir():
        print(f"{directory} is not a valid directory.")
        return

    for path in directory.iterdir():
        try:
            if path.is_file():
                path.unlink()
                print(f"Removed file: {path}")
            elif path.is_dir():
                path.rmdir()
                print(f"Removed directory: {path}")
        except Exception as e:
            print(f"Error removing {path}: {e}")


Client()
print("Validating diaspora is ready, this might take up to 3 minutes...")
if block_until_ready(max_minutes=3):
    print("Diaspora is ready!")
else:
    print("Diaspora unreachable. Clearing cache and retrying...")
    remove_files_and_directories("~/.diaspora")
    Client()
    print("Validating diaspora is ready, this might take up to 5 minutes...")
    if block_until_ready():
        print("Diaspora is ready!")
    else:
        print("Diaspora is still not ready.")
        exit(1)
