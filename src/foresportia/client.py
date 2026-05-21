"""Synchronous client for the Foresportia API."""

from __future__ import annotations

import os
from typing import Any, Optional

import httpx

from .exceptions import (
    ForesportiaAPIError,
    ForesportiaAuthError,
    ForesportiaConfigurationError,
    ForesportiaRateLimitError,
)

DEFAULT_BASE_URL = "https://api.foresportia.com"
DEFAULT_TIMEOUT = 20.0


class ForesportiaClient:
    """Synchronous Foresportia API client."""

    def __init__(
        self,
        api_key: str,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        if not api_key or not api_key.strip():
            raise ForesportiaConfigurationError("A non-empty Foresportia API key is required.")

        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client = httpx.Client(
            base_url=self.base_url,
            headers={"X-API-Key": api_key.strip()},
            timeout=timeout,
        )

    @classmethod
    def from_env(
        cls,
        env_var: str = "FORES_API_KEY",
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> "ForesportiaClient":
        """Create a client from an environment variable."""

        api_key = os.getenv(env_var)
        if not api_key:
            raise ForesportiaConfigurationError(
                f"Missing Foresportia API key. Set the {env_var} environment variable."
            )
        return cls(api_key=api_key, base_url=base_url, timeout=timeout)

    def close(self) -> None:
        """Close the underlying HTTP client."""

        self._client.close()

    def __enter__(self) -> "ForesportiaClient":
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()

    def me(self) -> dict[str, Any]:
        """Return details for the current API key."""

        return self._get("/v1/me")

    def usage(self) -> dict[str, Any]:
        """Return usage information for the current API key."""

        return self._get("/v1/me/usage")

    def picks_today(self) -> dict[str, Any]:
        """Return today's Foresportia picks."""

        return self._get("/v1/picks/today")

    def matches_today(self) -> dict[str, Any]:
        """Return today's matches."""

        return self._get("/v1/matches/today")

    def leagues(self) -> dict[str, Any]:
        """Return available football leagues."""

        return self._get("/v1/leagues")

    def league_matches(
        self,
        league_code: str,
        include: str = "upcoming",
        days: int = 31,
        limit: int = 100,
        start: Optional[str] = None,
    ) -> dict[str, Any]:
        """Return matches for a league."""

        path = f"/v1/leagues/{league_code}/matches"
        params: dict[str, Any] = {
            "include": include,
            "days": days,
            "limit": limit,
        }
        if start is not None:
            params["start"] = start
        return self._get(path, params=params)

    def world_cup_2026_matches(
        self,
        include: str = "all",
        days: int = 31,
        limit: int = 100,
        start: Optional[str] = None,
    ) -> dict[str, Any]:
        """Return FIFA World Cup 2026 matches."""

        return self.league_matches(
            "WORLD_CUP_2026",
            include=include,
            days=days,
            limit=limit,
            start=start,
        )

    def _get(self, path: str, params: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        try:
            response = self._client.get(path, params=params)
        except httpx.RequestError as exc:
            raise ForesportiaAPIError(
                f"Request to Foresportia API failed for {path}: {exc.__class__.__name__}",
                endpoint=path,
            ) from exc

        if response.status_code >= 400:
            self._raise_for_error(response, path)

        try:
            data = response.json()
        except ValueError as exc:
            raise ForesportiaAPIError(
                f"Foresportia API returned invalid JSON for {path}.",
                status_code=response.status_code,
                response_text=_short_response_text(response),
                endpoint=path,
            ) from exc

        if not isinstance(data, dict):
            raise ForesportiaAPIError(
                f"Foresportia API returned an unexpected response type for {path}.",
                status_code=response.status_code,
                response_text=_short_response_text(response),
                endpoint=path,
            )
        return data

    def _raise_for_error(self, response: httpx.Response, path: str) -> None:
        response_text = _short_response_text(response)
        message = (
            f"Foresportia API error for {path}: "
            f"HTTP {response.status_code}. {response_text}"
        ).strip()

        kwargs = {
            "status_code": response.status_code,
            "response_text": response_text,
            "endpoint": path,
        }

        if response.status_code in (401, 403):
            if response.status_code == 401:
                auth_message = f"Foresportia authentication failed for {path}: invalid API key."
            else:
                auth_message = (
                    f"Foresportia authorization failed for {path}: access is forbidden "
                    "for this API key."
                )
            raise ForesportiaAuthError(auth_message, **kwargs)

        if response.status_code == 429:
            raise ForesportiaRateLimitError(
                f"Foresportia rate limit exceeded for {path}.", **kwargs
            )

        raise ForesportiaAPIError(message, **kwargs)


def _short_response_text(response: httpx.Response, max_length: int = 500) -> str:
    text = response.text.replace("\n", " ").strip()
    if len(text) <= max_length:
        return text
    return f"{text[:max_length].rstrip()}..."
