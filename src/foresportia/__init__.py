"""Python SDK for the Foresportia API."""

from ._version import __version__
from .client import ForesportiaClient
from .exceptions import (
    ForesportiaAPIError,
    ForesportiaAuthenticationError,
    ForesportiaAuthError,
    ForesportiaAuthorizationError,
    ForesportiaConcurrencyLimitError,
    ForesportiaConfigurationError,
    ForesportiaError,
    ForesportiaNotFoundError,
    ForesportiaRateLimitError,
    ForesportiaServerError,
    ForesportiaTransportError,
    ForesportiaValidationError,
)
from .models import (
    ApiResponse,
    BulkItemError,
    BulkResult,
    League,
    MatchDetail,
    MatchSummary,
    Quota,
)

__all__ = [
    "ApiResponse",
    "BulkItemError",
    "BulkResult",
    "ForesportiaAPIError",
    "ForesportiaAuthError",
    "ForesportiaAuthenticationError",
    "ForesportiaAuthorizationError",
    "ForesportiaClient",
    "ForesportiaConcurrencyLimitError",
    "ForesportiaConfigurationError",
    "ForesportiaError",
    "ForesportiaNotFoundError",
    "ForesportiaRateLimitError",
    "ForesportiaServerError",
    "ForesportiaTransportError",
    "ForesportiaValidationError",
    "League",
    "MatchDetail",
    "MatchSummary",
    "Quota",
    "__version__",
]
