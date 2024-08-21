# flake8: noqa
"""A system for orchestrating the actions of multiple robots and scientific instruments to autonomously perform generalized experiments"""

from pathlib import Path

from wei.utils import extract_version

# __version__ = extract_version(Path(__file__).parent.parent / "pyproject.toml")
__version__ = "0.6.0"

# Alias "ExperimentClient" -> "Experiment" for backwards compatibility
from wei.experiment_client import ExperimentClient
from wei.experiment_client import ExperimentClient as Experiment
