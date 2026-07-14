"""Exceptions raised by the Foresportia SDK.

Hierarchy::

    ForesportiaError
    ├── ForesportiaConfigurationError
    └── ForesportiaAPIError
        ├── ForesportiaTransportError      (network / timeout, no HTTP response)
        ├── ForesportiaValidationError     (400 / 422, and client-side validation)
        ├── ForesportiaAuthError
        │   ├── ForesportiaAuthenticationError   (401)
        │   └── ForesportiaAuthorizationError    (403)
        ├── ForesportiaNotFoundError       (404)
        ├── ForesportiaRateLimitError      (429)
        │   └── ForesportiaConcurrencyLimitError (429, concurrency_limit_exceeded)
        └── ForesportiaServerError         (5xx)

The API key is never included in exception messages or attributes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .models import Quota


class ForesportiaError(Exception):
    """Base exception for all Foresportia SDK errors."""


class ForesportiaConfigurationError(ForesportiaError):
    """Raised when the SDK is not configured correctly."""


class ForesportiaAPIError(ForesportiaError):
    """Raised when the Foresportia API returns an error or invalid response."""

    def __init__(
        self,
        message: str,
        *,
        status_code: Optional[int] = None,
        response_text: Optional[str] = None,
        endpoint: Optional[str] = None,
        error_code: Optional[str] = None,
        quota: Optional["Quota"] = None,
        retry_after: Optional[int] = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.response_text = response_text
        self.endpoint = endpoint
        self.error_code = error_code
        self.quota = quota
        self.retry_after = retry_after


class ForesportiaTransportError(ForesportiaAPIError):
    """Raised when the request fails at the network level (no HTTP response)."""


class ForesportiaValidationError(ForesportiaAPIError):
    """Raised on HTTP 400/422 responses or invalid arguments detected client-side."""


class ForesportiaAuthError(ForesportiaAPIError):
    """Raised when authentication or authorization fails."""


class ForesportiaAuthenticationError(ForesportiaAuthError):
    """Raised on HTTP 401: the API key is missing, invalid, or revoked."""


class ForesportiaAuthorizationError(ForesportiaAuthError):
    """Raised on HTTP 403: the API key is valid but access is forbidden."""


class ForesportiaNotFoundError(ForesportiaAPIError):
    """Raised on HTTP 404: the requested resource does not exist."""


class ForesportiaRateLimitError(ForesportiaAPIError):
    """Raised on HTTP 429: a rate limit or quota was exceeded."""


class ForesportiaConcurrencyLimitError(ForesportiaRateLimitError):
    """Raised on HTTP 429 with the ``concurrency_limit_exceeded`` business code."""


class ForesportiaServerError(ForesportiaAPIError):
    """Raised on HTTP 5xx responses."""
