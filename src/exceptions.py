class CollectorError(Exception):
    """Base class for all errors raised by this project"""

class ConfigError(CollectorError):
    """A required setting is missing"""

class APIConnectionError(CollectorError):
    """Network Problem"""

class APIResponseError(CollectorError):
    """The API answered but with an error status or an unusable body"""

    def __init__(self,message:str,status_code:int | None=None ):
        super().__init__(message)
        self.status_code = status_code

class DataValidationError(CollectorError):
    """Too much of the incoming data is invalid"""

class StorageError(CollectorError):
    """A file could not be written or read"""
    