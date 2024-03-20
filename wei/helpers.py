"""Helper functions for WEI internals.
Imports are intentionally kept to a minimum and tightly scoped
to avoid circular dependencies."""

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


def initialize_state() -> None:
    """
    Initializes the state of the workcell from the workcell definition.
    """
    from wei.config import Config
    from wei.core.data_classes import Workcell
    from wei.core.location import initialize_workcell_locations
    from wei.core.module import initialize_workcell_modules
    from wei.core.state_manager import StateManager

    state_manager = StateManager()
    state_manager.set_workcell(Workcell.from_yaml(Config.workcell_file))
    initialize_workcell_modules()
    initialize_workcell_locations()


def parse_args() -> Namespace:
    """Parse WEI's command line arguments and populate the config."""
    from argparse import ArgumentParser
    from pathlib import Path
    from typing import get_type_hints

    from wei.config import Config
    from wei.core.data_classes import PathLike, WorkcellConfig
    from wei.core.workcell import load_workcell_file

    parser = ArgumentParser()
    parser.add_argument(
        "--workcell", type=Path, help="Path to workcell file", required=True
    )
    field_type_map = get_type_hints(WorkcellConfig)
    for name, field in WorkcellConfig.model_fields.items():
        field_type = field_type_map[name]
        if field_type == PathLike:
            field_type = Path
        elif field_type == bool:
            field_type = string_to_bool
        parser.add_argument(
            f"--{name}",
            help=field.description,
            type=field_type,
            default=None,
        )
    args = parser.parse_args()
    load_workcell_file(args.workcell)
    for argument, value in vars(args).items():
        if value is not None:
            setattr(Config, argument, value)
    Config.configured = True
