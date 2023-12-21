"""Helper functions for WEI internals.
Imports are intentionally kept to a minimum and tightly scoped
to avoid circular dependencies."""

from argparse import Namespace


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
    from wei.core.data_classes import WorkcellData
    from wei.core.location import initialize_workcell_locations
    from wei.core.module import initialize_workcell_modules
    from wei.core.state_manager import StateManager

    state_manager = StateManager()
    state_manager.set_workcell(WorkcellData.from_yaml(Config.workcell_file))
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
