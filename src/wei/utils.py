"""Helper functions for WEI internals.
Imports are intentionally kept to a minimum and tightly scoped
to avoid circular dependencies."""

import csv
from argparse import Namespace
from pathlib import Path
from typing import Optional, Union


def extract_version(pyproject_path: Optional[Union[Path, str]]) -> str:
    """Returns either the version of the installed package or the one
    found in the project's pyproject.toml, if provided"""
    import importlib.metadata
    from contextlib import suppress

    if pyproject_path is not None:
        with suppress(FileNotFoundError, StopIteration):
            with open(
                pyproject_path,
                encoding="utf-8",
            ) as pyproject_toml:
                version = (
                    next(line for line in pyproject_toml if line.startswith("version"))
                    .split("=")[1]
                    .strip("'\"\n ")
                )
                return f"{version}"
    try:
        return importlib.metadata.version(
            __package__ or __name__.split(".", maxsplit=1)[0]
        )
    except Exception:
        return "unknown"


def string_to_bool(string: str) -> bool:
    """Convert a string to a boolean value."""
    from argparse import ArgumentTypeError

    if string.lower() in ("true", "t", "1", "yes", "y"):
        return True
    elif string.lower() in ("false", "f", "0", "no", "n"):
        return False
    else:
        raise ArgumentTypeError(f"Invalid boolean value: {string}")


def initialize_state(workcell=None) -> None:
    """
    Initializes the state of the workcell from the workcell definition.
    """
    from wei.config import Config
    from wei.core.location import initialize_workcell_locations
    from wei.core.module import initialize_workcell_modules
    from wei.core.state_manager import state_manager
    from wei.types import ModuleStatus, Workcell

    if not workcell:
        workcell = Workcell.from_yaml(Config.workcell_file)
    state_manager.set_workcell(workcell)
    state_manager.wc_status = ModuleStatus.IDLE
    initialize_workcell_modules()
    initialize_workcell_locations()


def parse_args() -> Namespace:
    """Parse WEI's command line arguments and populate the config."""
    from argparse import ArgumentParser
    from pathlib import Path
    from typing import get_type_hints

    from wei.config import Config
    from wei.core.workcell import load_workcell_file
    from wei.types import PathLike, WorkcellConfig

    parser = ArgumentParser()
    parser.add_argument(
        "--workcell", type=Path, help="Path to workcell file", required=False
    )
    field_type_map = get_type_hints(WorkcellConfig)
    for name, field in WorkcellConfig.model_fields.items():
        field_type = field_type_map[name]
        if field_type is PathLike:
            field_type = Path
        elif field_type is bool:
            field_type = string_to_bool
        parser.add_argument(
            f"--{name}",
            help=field.description,
            type=field_type,
        )
    cli_args = parser.parse_args()
    load_workcell_file(cli_args.workcell)
    for argument, value in vars(cli_args).items():
        if value is not None:
            setattr(Config, argument, value)
    Config.configured = True


def flatten_json(json_data, parent_key="", sep="_"):
    """Converts nested json data to a flat dictionary"""
    items = []
    for key, value in json_data.items():
        new_key = parent_key + sep + key if parent_key else key
        if isinstance(value, dict):
            items.extend(flatten_json(value, new_key, sep=sep).items())
        else:
            items.append((new_key, value))
    return dict(items)


def json_to_csv(json_data, csv_file_path):
    """Converts json data to a csv file"""
    flattened_data = [flatten_json(record) for record in json_data]
    fieldnames = flattened_data[0].keys()
    with open(csv_file_path, "w", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(flattened_data)


def threaded_task(func):
    """Mark a function as a threaded task, to be run without awaiting. Returns the thread object, so you _can_ await if needed."""

    import functools
    import threading

    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> threading.Thread:
        thread = threading.Thread(target=func, args=args, kwargs=kwargs)
        thread.start()
        return thread

    return wrapper


def threaded_daemon(func):
    """Mark a function as a threaded daemon, to be run without awaiting. Returns the thread object, so you _can_ await if needed, and stops when the calling thread terminates."""

    import functools
    import threading

    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> threading.Thread:
        thread = threading.Thread(target=func, args=args, kwargs=kwargs)
        thread.daemon = True
        thread.start()
        return thread

    return wrapper


def pretty_type_repr(type_hint):
    """Returns a pretty string representation of a type hint, including subtypes."""
    type_name = type_hint.__name__
    if (
        "__args__" in dir(type_hint) and type_hint.__args__
    ):  # * If the type has subtype info
        type_name += "["
        for subtype in type_hint.__args__:
            type_name += pretty_type_repr(subtype)
        type_name += "]"
    return type_name


class classproperty:
    """Provides a simple class property decorator for class-level getter properties. Credit: https://stackoverflow.com/a/76301341"""

    def __init__(self, func):
        """Initialize the classproperty with the getter function."""
        self.fget = func

    def __get__(self, instance, owner):
        """Return the result of the getter function."""
        return self.fget(owner)
