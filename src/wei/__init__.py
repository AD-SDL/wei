# flake8: noqa
"""A system for orchestrating the actions of multiple robots and scientific instruments to autonomously perform generalized experiments"""

from importlib.metadata import PackageNotFoundError, version

__version__ = "unknown"
try:
    __version__ = version(__package__)
except PackageNotFoundError:
    __version__ = version("ad_sdl.wei")
except PackageNotFoundError:
    __version__ = version("wei")

# Alias "ExperimentClient" -> "Experiment" for backwards compatibility
from wei.experiment_client import ExperimentClient
from wei.experiment_client import ExperimentClient as Experiment

__all__ = [
    "Experiment",
    "ExperimentClient",
    "__version__",
]
