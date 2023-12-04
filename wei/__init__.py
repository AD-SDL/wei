# flake8: noqa
"""A system for orchestrating the actions of multiple robots and scientific instruments to autonomously perform generalized experiments"""
__version__ = "0.5.1.dev0"

# Alias "ExperimentClient" -> "Experiment" for backwards compatibility
from wei.experiment_client import ExperimentClient
from wei.experiment_client import ExperimentClient as Experiment
