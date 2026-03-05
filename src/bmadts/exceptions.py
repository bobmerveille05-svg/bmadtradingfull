from __future__ import annotations


class BMADException(Exception):
    pass


class UserInputError(BMADException):
    pass


class BMADValidationError(BMADException):
    pass


class FileSystemError(BMADException):
    pass


class LLMError(BMADException):
    pass


class CodeGenerationError(BMADException):
    pass


class TestingError(BMADException):
    pass


class StateManagementError(BMADException):
    pass


class ConfigValidationError(BMADValidationError):
    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__("Invalid configuration")


class SessionNotFoundError(FileSystemError):
    pass


class CommandError(UserInputError):
    pass


class InvalidTransitionError(StateManagementError):
    pass


class GateNotPassedError(StateManagementError):
    pass
