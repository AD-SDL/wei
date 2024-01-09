# flake8: noqa
"""A system for orchestrating the actions of multiple robots and scientific instruments to autonomously perform generalized experiments"""

from wei.helpers import extract_version
from pathlib import Path


__version__ = extract_version(Path(__file__).parent.parent / "pyproject.toml")

# Alias "ExperimentClient" -> "Experiment" for backwards compatibility
from wei.experiment_client import ExperimentClient
from wei.experiment_client import ExperimentClient as Experiment
