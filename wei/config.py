"""
Handles the configuration of the engine and server.
"""

from typing import Dict


class Config:
    """
    Allows for shared configuration across the application
    Parameters are determined by WorkcellConfig dataclass
    """

    configured = False
    test = False

    def dump_to_json(self) -> Dict:
        """
        Returns the configuration as a dictionary
        """
        return self.__dict__
