"""Exceptions for WEI"""


class WorkflowFailedException(Exception):
    """Raised when a workflow fails"""

    def __init__(self, message: str):
        """Initializes the exception"""
        super().__init__(message)
        self.message = message
