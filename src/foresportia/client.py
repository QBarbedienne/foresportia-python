"""Synchronous client for the Foresportia API."""

from __future__ import annotations

import datetime as _dt
import os
import re
import time
from typing import Any, Iterator, Optional, Union
from urllib.parse import urlsplit

import httpx

from ._version import __version__
from .exceptions import (
    ForesportiaAPIError,
    ForesportiaAuthenticationError,
    ForesportiaAuthorizationError,
    ForesportiaConcurrencyLimitError,
    ForesportiaConfigurationError,
    ForesportiaNotFoundError,
    ForesportiaRateLimitError,
    ForesportiaServerError,
    ForesportiaTransportError,
    ForesportiaValidationError,
)
from .models import (
    ApiResponse,
    BulkResult,
    League,
    MatchDetail,
    MatchSummary,
    Quota,
)

DEFAULT_BASE_URL = "https://api.foresportia.com"
DEFAULT_TIMEOUT = 20.0
DEFAULT_MAX_RETRIES = 0

MATCH_ID_RE = re.compile(r"^fsm:v1:[a-f0-9]{64}$")
BULK_MAX_MATCH_IDS = 100

_RETRYABLE_STATUS = frozenset({502, 503, 504})
_MAX_BACKOFF_SECONDS = 8.0
_MAX_RETRY_AFTER_SECONDS = 60.0
_LOCAL_HOSTS = frozenset({"localhost", "127.0.0.1", "::1"})


def _validate_base_url(base_url: str, allow_insecure: bool) -> str:
    parts = urlsplit(base_url)
    scheme = (parts.scheme or "").lower()
    host = (parts.hostname or "").lower()
    if scheme == "https":
        return base_url.rstrip("/")
    if scheme == "http" and (host in _LOCAL_HOSTS or allow_insecure):
        return base_url.rstrip("/")
    raise ForesportiaConfigurationError(
        "The Foresportia base URL must use HTTPS. Plain HTTP is only allowed for "
        "localhost, or with allow_insecure_base_url=True for development."
    )


def _as_date_str(value: Union[str, _dt.date, None]) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, _dt.datetime):
        return value.date().isoformat()
    if isinstance(value, _dt.date):
        return value.isoformat()
    return str(value)


class ForesportiaClient:
    """Synchronous Foresportia API client.

    Authentication uses the ``X-API-Key`` header only; the key never appears
    in URLs, ``repr``, logs, or exceptions. Prefer loading the key from an
    environment variable with :meth:`from_env`.

    Args:
        api_key: Your Foresportia API key.
        base_url: API root. Must be HTTPS (HTTP is allowed for localhost, or
            with ``allow_insecure_base_url=True`` for development/testing).
        timeout: Request timeout in seconds (or an ``httpx.Timeout``).
        max_retries: Extra attempts for GET requests after network errors or
            502/503/504 responses, with bounded exponential backoff. Disabled
            by default (``0``): a request that times out client-side may still
            have been processed and counted against your quota server-side, so
            each retry can consume an extra quota unit. Enable explicitly
            (e.g. ``max_retries=2``) if that trade-off is acceptable.
        retry_on_rate_limit: When ``True``, a 429 response is retried after
            honoring ``Retry-After`` (bounded). Disabled by default.
        allow_insecure_base_url: Allow a plain-HTTP base URL (development only).
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = DEFAULT_BASE_URL,
        timeout: Union[float, httpx.Timeout] = DEFAULT_TIMEOUT,
        *,
        max_retries: int = DEFAULT_MAX_RETRIES,
        retry_on_rate_limit: bool = False,
        allow_insecure_base_url: bool = False,
    ) -> None:
        if not api_key or not api_key.strip():
            raise ForesportiaConfigurationError("A non-empty Foresportia API key is required.")
        if max_retries < 0:
            raise ForesportiaConfigurationError("max_retries must be >= 0.")

        self.base_url = _validate_base_url(base_url, allow_insecure_base_url)
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_on_rate_limit = retry_on_rate_limit
        self._client = httpx.Client(
            base_url=self.base_url,
            headers={
                "X-API-Key": api_key.strip(),
                "User-Agent": f"foresportia-python/{__version__}",
            },
            timeout=timeout,
        )

    def __repr__(self) -> str:  # never expose the API key
        return f"ForesportiaClient(base_url={self.base_url!r})"

    @classmethod
    def from_env(
        cls,
        env_var: str = "FORES_API_KEY",
        base_url: str = DEFAULT_BASE_URL,
        timeout: Union[float, httpx.Timeout] = DEFAULT_TIMEOUT,
        **kwargs: Any,
    ) -> "ForesportiaClient":
        """Create a client from an environment variable."""

        api_key = os.getenv(env_var)
        if not api_key:
            raise ForesportiaConfigurationError(
                f"Missing Foresportia API key. Set the {env_var} environment variable."
            )
        return cls(api_key=api_key, base_url=base_url, timeout=timeout, **kwargs)

    def close(self) -> None:
        """Close the underlying HTTP client."""

        self._client.close()

    def __enter__(self) -> "ForesportiaClient":
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()

    # ------------------------------------------------------------------ #
    # Typed public API                                                    #
    # ------------------------------------------------------------------ #

    def list_leagues(self, *, etag: Optional[str] = None) -> ApiResponse[list[League]]:
        """List the competitions available to the current API key.

        ``GET /v1/leagues``
        """

        return self._request_typed(
            "GET",
            "/v1/leagues",
            etag=etag,
            parse=lambda payload: [
                League.from_dict(item)
                for item in payload.get("leagues", [])
                if isinstance(item, dict)
            ],
        )

    def list_league_matches(
        self,
        league_code: str,
        *,
        include: str = "upcoming",
        start: Union[str, _dt.date, None] = None,
        days: Optional[int] = 14,
        limit: int = 200,
        cursor: Optional[str] = None,
        etag: Optional[str] = None,
    ) -> ApiResponse[list[MatchSummary]]:
        """List matches for a competition over a date window.

        ``GET /v1/leagues/{code}/matches``

        Args:
            league_code: Competition code, e.g. ``"PREMIER_LEAGUE"``.
            include: ``"upcoming"``, ``"past"``, or ``"all"``.
            start: Window start date (``YYYY-MM-DD`` or ``datetime.date``).
                Defaults server-side to today.
            days: Window size in days (1..31). Defaults to ``14``; pass ``None``
                to omit the parameter entirely and let the server apply its own
                default window for the request.
            limit: Maximum matches returned (1..500).
            cursor: Opaque continuation cursor returned by ``response.next_cursor``.
            etag: Previous ``ETag`` for conditional requests.
        """

        code = str(league_code or "").strip()
        if not code:
            raise ForesportiaValidationError("league_code must be a non-empty string.")
        params: dict[str, Any] = {"include": include, "limit": limit}
        if days is not None:
            params["days"] = days
        start_str = _as_date_str(start)
        if start_str is not None:
            params["start"] = start_str
        if cursor is not None:
            params["cursor"] = cursor
        return self._request_typed(
            "GET",
            f"/v1/leagues/{code}/matches",
            params=params,
            etag=etag,
            parse=_parse_match_summaries,
        )

    def iter_league_matches(
        self,
        league_code: str,
        *,
        include: str = "upcoming",
        start: Union[str, _dt.date, None] = None,
        days: Optional[int] = 14,
        limit: int = 200,
        cursor: Optional[str] = None,
        max_pages: Optional[int] = None,
        max_matches: Optional[int] = None,
    ) -> Iterator[MatchSummary]:
        """Iterate lazily over deterministic league-match pages.

        ``days`` defaults to ``14``; pass ``None`` to omit the parameter and let
        the server apply its own default window. ``max_pages`` and
        ``max_matches`` bound client-side work. A repeated server cursor raises
        :class:`ForesportiaAPIError` instead of looping.
        """

        if max_pages is not None and max_pages < 1:
            raise ForesportiaValidationError("max_pages must be >= 1.")
        if max_matches is not None and max_matches < 1:
            raise ForesportiaValidationError("max_matches must be >= 1.")
        next_cursor = cursor
        seen_cursors = {cursor} if cursor is not None else set()
        pages = 0
        yielded = 0
        while max_pages is None or pages < max_pages:
            page = self.list_league_matches(
                league_code,
                include=include,
                start=start,
                days=days,
                limit=limit,
                cursor=next_cursor,
            )
            pages += 1
            for match in page.data or []:
                yield match
                yielded += 1
                if max_matches is not None and yielded >= max_matches:
                    return
            next_cursor = page.next_cursor
            if not next_cursor:
                return
            if next_cursor in seen_cursors:
                raise ForesportiaAPIError(
                    "Foresportia API returned a repeated pagination cursor.",
                    endpoint=f"/v1/leagues/{league_code}/matches",
                    error_code="repeated_cursor",
                )
            seen_cursors.add(next_cursor)

    def list_league_history(
        self,
        league_code: str,
        *,
        start: Union[str, _dt.date, None] = None,
        days: Optional[int] = None,
        limit: int = 200,
        cursor: Optional[str] = None,
        etag: Optional[str] = None,
    ) -> ApiResponse[list[MatchSummary]]:
        """List past matches for a competition (``include="past"``).

        Thin wrapper around :meth:`list_league_matches` that always requests
        finished matches. The return type, metadata (``next_cursor``,
        ``history_available_from``, ``quota``, ``etag``, ``not_modified``) and
        typed errors are identical to the underlying method.

        When ``days`` is left as ``None`` (the default) the ``days`` parameter is
        omitted from the request, so the **server** resolves the window from the
        key's real history entitlement (capped at the 31-day per-request
        maximum). The SDK never resolves the entitlement locally and issues no
        extra discovery call: the first history request is self-contained.
        Passing an explicit ``days`` forwards exactly that value; the server
        keeps its own validation and error behaviour for values beyond the
        entitlement or the 31-day maximum — nothing is silently truncated.

        Entitlement stays server-side: Developer keys currently expose 7 days of
        history and Starter keys 90 rolling days, while an automatic request is
        capped at 31 days. A valid window may legitimately contain no matches.

        Args:
            league_code: Competition code, e.g. ``"SUE"``.
            start: Window start date (``YYYY-MM-DD`` or ``datetime.date``).
                Defaults server-side to the start of the available window.
            days: Window size in days (1..31), or ``None`` (default) to let the
                server choose the window from the entitlement.
            limit: Maximum matches returned (1..500).
            cursor: Opaque continuation cursor returned by ``response.next_cursor``.
            etag: Previous ``ETag`` for conditional requests.
        """

        return self.list_league_matches(
            league_code,
            include="past",
            start=start,
            days=days,
            limit=limit,
            cursor=cursor,
            etag=etag,
        )

    def iter_league_history(
        self,
        league_code: str,
        *,
        start: Union[str, _dt.date, None] = None,
        days: Optional[int] = None,
        limit: int = 200,
        cursor: Optional[str] = None,
        max_pages: Optional[int] = None,
        max_matches: Optional[int] = None,
    ) -> Iterator[MatchSummary]:
        """Iterate lazily over past matches for a competition (``include="past"``).

        Thin wrapper around :meth:`iter_league_matches` that always requests
        finished matches. When ``days`` is ``None`` (the default) the parameter
        is omitted on every page, so the server resolves the window from the
        entitlement (capped at 31 days per request); an explicit ``days`` is
        forwarded unchanged. Pagination, ``next_cursor`` handling, the
        repeated-cursor guard, and propagated exceptions are unchanged; pages
        are fetched on demand rather than buffered in memory.

        This only paginates the single resolved window (at most 31 days). It
        does not automatically walk the full 90-day Starter entitlement across
        several windows.
        """

        yield from self.iter_league_matches(
            league_code,
            include="past",
            start=start,
            days=days,
            limit=limit,
            cursor=cursor,
            max_pages=max_pages,
            max_matches=max_matches,
        )

    def get_match(
        self,
        match_id: str,
        *,
        include: Optional[str] = None,
        etag: Optional[str] = None,
    ) -> ApiResponse[MatchDetail]:
        """Fetch the full payload for one match.

        ``GET /v1/matches/{match_id}``

        Public match IDs look like ``fsm:v1:<64 hex chars>``. Pass IDs exactly
        as returned by list endpoints; the SDK never rewrites them.

        Args:
            match_id: Public match identifier.
            include: Optional comma-separated sections where supported by the API.
            etag: Previous ``ETag`` for conditional requests.
        """

        identifier = str(match_id or "").strip()
        if not identifier:
            raise ForesportiaValidationError("match_id must be a non-empty string.")
        params = {"include": include} if include is not None else None
        return self._request_typed(
            "GET",
            f"/v1/matches/{identifier}",
            params=params,
            etag=etag,
            parse=lambda payload: MatchDetail(raw=payload),
        )

    def get_matches_bulk(
        self,
        match_ids: list[str],
        *,
        etag: Optional[str] = None,
    ) -> ApiResponse[BulkResult]:
        """Fetch matches in bulk (Developer: 5; Starter: 100).

        ``POST /v1/matches/bulk``

        The SDK enforces only the API-wide technical ceiling of 100 unique
        ``fsm:v1:<64 hex>`` identifiers. The server remains authoritative for
        the lower plan limit. Request order is preserved and
        per-ID failures are reported in ``response.data.errors`` (for example
        ``match_not_found``) without hiding the successful results.
        """

        self._validate_bulk_ids(match_ids)
        return self._request_typed(
            "POST",
            "/v1/matches/bulk",
            json_body={"match_ids": list(match_ids)},
            etag=etag,
            parse=BulkResult.from_dict,
        )

    def list_today_matches(self, *, etag: Optional[str] = None) -> ApiResponse[list[MatchSummary]]:
        """List today's matches across the competitions available to the key.

        ``GET /v1/matches/today``
        """

        return self._request_typed(
            "GET",
            "/v1/matches/today",
            etag=etag,
            parse=_parse_match_summaries,
        )

    def list_today_picks(
        self,
        *,
        limit: int = 20,
        etag: Optional[str] = None,
    ) -> ApiResponse[list[MatchSummary]]:
        """List today's highest-confidence picks (1..100).

        ``GET /v1/picks/today``
        """

        return self._request_typed(
            "GET",
            "/v1/picks/today",
            params={"limit": limit},
            etag=etag,
            parse=_parse_match_summaries,
        )

    @staticmethod
    def _validate_bulk_ids(match_ids: list[str]) -> None:
        if not isinstance(match_ids, (list, tuple)):
            raise ForesportiaValidationError("match_ids must be a list of strings.")
        if not 1 <= len(match_ids) <= BULK_MAX_MATCH_IDS:
            raise ForesportiaValidationError(
                f"match_ids must contain between 1 and {BULK_MAX_MATCH_IDS} IDs "
                f"(got {len(match_ids)})."
            )
        if any(not isinstance(value, str) for value in match_ids):
            raise ForesportiaValidationError("match_ids must contain strings only.")
        if len(match_ids) != len(set(match_ids)):
            raise ForesportiaValidationError("match_ids must not contain duplicates.")
        invalid = [value for value in match_ids if MATCH_ID_RE.fullmatch(value) is None]
        if invalid:
            raise ForesportiaValidationError(
                "Invalid match ID format (expected fsm:v1:<64 hex chars>): "
                + ", ".join(invalid[:3])
            )

    # ------------------------------------------------------------------ #
    # Legacy dict-based API (kept for backward compatibility)             #
    # ------------------------------------------------------------------ #

    def me(self) -> dict[str, Any]:
        """Return details for the current API key."""

        return self._get("/v1/me")

    def health(self) -> dict[str, Any]:
        """Return the tolerant public ``GET /v1/health`` payload."""

        return self._get("/v1/health")

    def usage(self) -> dict[str, Any]:
        """Return usage information for the current API key."""

        return self._get("/v1/me/usage")

    def picks_today(self) -> dict[str, Any]:
        """Return today's Foresportia picks as a raw dict.

        Prefer :meth:`list_today_picks` for typed results and metadata.
        """

        return self._get("/v1/picks/today")

    def matches_today(self) -> dict[str, Any]:
        """Return today's matches as a raw dict.

        Prefer :meth:`list_today_matches` for typed results and metadata.
        """

        return self._get("/v1/matches/today")

    def leagues(self) -> dict[str, Any]:
        """Return available football leagues as a raw dict.

        Prefer :meth:`list_leagues` for typed results and metadata.
        """

        return self._get("/v1/leagues")

    def league_matches(
        self,
        league_code: str,
        include: str = "upcoming",
        days: int = 31,
        limit: int = 100,
        start: Optional[str] = None,
    ) -> dict[str, Any]:
        """Return matches for a league as a raw dict.

        Prefer :meth:`list_league_matches` for typed results and metadata.
        """

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

    # ------------------------------------------------------------------ #
    # HTTP plumbing                                                       #
    # ------------------------------------------------------------------ #

    def _get(self, path: str, params: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        response = self._send("GET", path, params=params)
        if response.status_code >= 400:
            self._raise_for_error(response, path)
        return self._parse_json_dict(response, path)

    def _request_typed(
        self,
        method: str,
        path: str,
        *,
        parse: Any,
        params: Optional[dict[str, Any]] = None,
        json_body: Optional[dict[str, Any]] = None,
        etag: Optional[str] = None,
    ) -> ApiResponse[Any]:
        headers = {"If-None-Match": etag} if etag else None
        response = self._send(method, path, params=params, json_body=json_body, headers=headers)

        quota = Quota.from_headers(response.headers)
        response_etag = response.headers.get("ETag")

        if response.status_code == 304:
            return ApiResponse(
                data=None,
                payload=None,
                etag=response_etag or etag,
                quota=quota,
                status_code=304,
            )
        if response.status_code >= 400:
            self._raise_for_error(response, path)

        payload = self._parse_json_dict(response, path)
        return ApiResponse(
            data=parse(payload),
            payload=payload,
            etag=response_etag,
            quota=quota,
            status_code=response.status_code,
        )

    def _send(
        self,
        method: str,
        path: str,
        *,
        params: Optional[dict[str, Any]] = None,
        json_body: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, str]] = None,
    ) -> httpx.Response:
        retryable = method == "GET" and self.max_retries > 0
        attempts = (self.max_retries if retryable else 0) + 1
        for attempt in range(attempts):
            last_attempt = attempt + 1 >= attempts
            try:
                response = self._client.request(
                    method, path, params=params, json=json_body, headers=headers
                )
            except httpx.RequestError as exc:
                if not last_attempt:
                    time.sleep(self._backoff(attempt))
                    continue
                raise ForesportiaTransportError(
                    f"Request to Foresportia API failed for {path}: {exc.__class__.__name__}",
                    endpoint=path,
                ) from exc

            if not last_attempt and retryable and response.status_code in _RETRYABLE_STATUS:
                time.sleep(self._backoff(attempt))
                continue
            if (
                response.status_code == 429
                and self.retry_on_rate_limit
                and self.max_retries > 0
                and attempt < self.max_retries
            ):
                retry_after = Quota.from_headers(response.headers).retry_after
                delay = min(
                    float(retry_after) if retry_after is not None else self._backoff(attempt),
                    _MAX_RETRY_AFTER_SECONDS,
                )
                time.sleep(max(delay, 0.0))
                continue
            return response
        raise AssertionError("unreachable")  # pragma: no cover

    @staticmethod
    def _backoff(attempt: int) -> float:
        return min(0.5 * (2**attempt), _MAX_BACKOFF_SECONDS)

    def _parse_json_dict(self, response: httpx.Response, path: str) -> dict[str, Any]:
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
        status = response.status_code
        response_text = _short_response_text(response)
        error_code = _extract_error_code(response)
        quota = Quota.from_headers(response.headers)

        kwargs: dict[str, Any] = {
            "status_code": status,
            "response_text": response_text,
            "endpoint": path,
            "error_code": error_code,
            "quota": quota,
            "retry_after": quota.retry_after,
        }

        if status == 401:
            raise ForesportiaAuthenticationError(
                f"Foresportia authentication failed for {path}: invalid API key.",
                **kwargs,
            )
        if status == 403:
            raise ForesportiaAuthorizationError(
                f"Foresportia authorization failed for {path}: access is forbidden "
                "for this API key.",
                **kwargs,
            )
        if status == 404:
            raise ForesportiaNotFoundError(
                f"Foresportia resource not found for {path}.", **kwargs
            )
        if status in (400, 422):
            raise ForesportiaValidationError(
                f"Foresportia rejected the request for {path}: "
                f"{error_code or response_text or 'invalid request'}",
                **kwargs,
            )
        if status == 429:
            if error_code == "concurrency_limit_exceeded":
                raise ForesportiaConcurrencyLimitError(
                    f"Foresportia concurrency limit exceeded for {path}.", **kwargs
                )
            raise ForesportiaRateLimitError(
                f"Foresportia rate limit exceeded for {path}.", **kwargs
            )
        if status >= 500:
            raise ForesportiaServerError(
                f"Foresportia server error for {path}: HTTP {status}.", **kwargs
            )
        raise ForesportiaAPIError(
            f"Foresportia API error for {path}: HTTP {status}. {response_text}".strip(),
            **kwargs,
        )


def _parse_match_summaries(payload: dict[str, Any]) -> list[MatchSummary]:
    return [
        MatchSummary.from_dict(item)
        for item in payload.get("matches", [])
        if isinstance(item, dict)
    ]


def _extract_error_code(response: httpx.Response) -> Optional[str]:
    try:
        body = response.json()
    except ValueError:
        return None
    if isinstance(body, dict):
        detail = body.get("detail")
        if isinstance(detail, str):
            return detail
    return None


def _short_response_text(response: httpx.Response, max_length: int = 500) -> str:
    text = response.text.replace("\n", " ").strip()
    if len(text) <= max_length:
        return text
    return f"{text[:max_length].rstrip()}..."
