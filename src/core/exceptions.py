from __future__ import annotations


class ModelError(Exception):
    """Raised when a statistical model cannot be executed reliably."""


class ValidationError(Exception):
    """Raised when input data or query state does not satisfy requirements."""


class QueryError(Exception):
    """Raised when a dataset query cannot be built or executed."""
