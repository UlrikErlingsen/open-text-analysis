"""Friendly domain errors for TextSignal."""


class DataProblem(ValueError):
    """Raised when an input cannot support the requested analysis."""


def friendly_message(exc: Exception) -> str:
    """Return a concise user-facing error without exposing internals."""
    if isinstance(exc, DataProblem):
        return str(exc)
    if isinstance(exc, (KeyError, ValueError, TypeError)):
        return f"TextSignal could not complete that request: {exc}"
    return "TextSignal hit an unexpected problem. Check the data roles and try again."

