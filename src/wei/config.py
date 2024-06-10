"""
Handles the configuration of the engine and server.
"""

from typing import Dict


class Config:
    """
    Allows for shared configuration across the application.
    Parameters are determined by WorkcellConfig dataclass in workcell_types.py
    """

    configured = False
    test = False

    @classmethod
    def dump_to_json(cls) -> Dict:
        """
        Returns the configuration as a dictionary
        """
        return cls.__dict__
