"""
Handles the configuration of the engine and server.
"""


class Config:
    """
    Allows for shared configuration across the application
    Parameters are determined by WorkcellConfig dataclass
    """

    configured = False
    test = False
