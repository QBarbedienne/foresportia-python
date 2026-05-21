"""Exceptions raised by the Foresportia SDK."""

from __future__ import annotations

from typing import Optional


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
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.response_text = response_text
        self.endpoint = endpoint


class ForesportiaAuthError(ForesportiaAPIError):
    """Raised when authentication or authorization fails."""


class ForesportiaRateLimitError(ForesportiaAPIError):
    """Raised when the Foresportia API rate limit is exceeded."""
