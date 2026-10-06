class CutoffFrameworkError(Exception):
    pass


class InputValidationError(CutoffFrameworkError, ValueError):
    pass


class InsufficientBinsError(CutoffFrameworkError, ValueError):
    """Raised when the response curve cannot meet the configured valid-bin minimum."""
