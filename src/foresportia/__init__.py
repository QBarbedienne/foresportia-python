"""Python SDK for the Foresportia API."""

from .client import ForesportiaClient
from .exceptions import (
    ForesportiaAPIError,
    ForesportiaAuthError,
    ForesportiaConfigurationError,
    ForesportiaError,
    ForesportiaRateLimitError,
)

__all__ = [
    "ForesportiaAPIError",
    "ForesportiaAuthError",
    "ForesportiaClient",
    "ForesportiaConfigurationError",
    "ForesportiaError",
    "ForesportiaRateLimitError",
]

__version__ = "0.1.0"
