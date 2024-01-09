# flake8: noqa
"""A system for orchestrating the actions of multiple robots and scientific instruments to autonomously perform generalized experiments"""
from contextlib import suppress
import importlib.metadata
from pathlib import Path


def _extract_version() -> str:
    """Returns either the version of the installed package or the one
    found in the project's pyproject.toml"""
    with suppress(FileNotFoundError, StopIteration):
        with open(
            (root_dir := Path(__file__).parent.parent) / "pyproject.toml",
            encoding="utf-8",
        ) as pyproject_toml:
            version = (
                next(line for line in pyproject_toml if line.startswith("version"))
                .split("=")[1]
                .strip("'\"\n ")
            )
            return f"{version}"
    return importlib.metadata.version(__package__ or __name__.split(".", maxsplit=1)[0])


__version__ = _extract_version()

# Alias "ExperimentClient" -> "Experiment" for backwards compatibility
from wei.experiment_client import ExperimentClient
from wei.experiment_client import ExperimentClient as Experiment
