"""Lightweight typed models for Foresportia API responses.

These models are intentionally tolerant: they expose the common fields with
types while keeping the full server payload available in ``raw``. New optional
fields added by the API never break parsing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Generic, Mapping, Optional, TypeVar

T = TypeVar("T")


def _to_int(value: Any) -> Optional[int]:
    if value is None:
        return None
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


@dataclass(frozen=True)
class Quota:
    """Quota and rate-limit metadata parsed from response headers.

    All fields are ``None`` when the corresponding header is absent. The SDK
    only reports these values; quota enforcement stays server-side.
    """

    limit: Optional[int] = None
    remaining: Optional[int] = None
    reset_at: Optional[int] = None
    units_remaining_hour: Optional[int] = None
    units_remaining_day: Optional[int] = None
    match_rows_remaining_day: Optional[int] = None
    retry_after: Optional[int] = None

    @classmethod
    def from_headers(cls, headers: Mapping[str, str]) -> "Quota":
        return cls(
            limit=_to_int(headers.get("X-RateLimit-Limit")),
            remaining=_to_int(headers.get("X-RateLimit-Remaining")),
            reset_at=_to_int(headers.get("X-RateLimit-Reset")),
            units_remaining_hour=_to_int(headers.get("X-Quota-Units-Remaining-Hour")),
            units_remaining_day=_to_int(headers.get("X-Quota-Units-Remaining-Day")),
            match_rows_remaining_day=_to_int(headers.get("X-Match-Rows-Remaining-Day")),
            retry_after=_to_int(headers.get("Retry-After")),
        )


@dataclass(frozen=True)
class League:
    """A competition entry from ``GET /v1/leagues``."""

    code: str
    name: Optional[str] = None
    country: Optional[str] = None
    catalog_status: Optional[str] = None
    activity_status: Optional[str] = None
    available: Optional[bool] = None
    matches_available: Optional[int] = None
    raw: dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "League":
        return cls(
            code=str(data.get("code", "")),
            name=data.get("name"),
            country=data.get("country"),
            catalog_status=data.get("catalog_status"),
            activity_status=data.get("activity_status"),
            available=data.get("available"),
            matches_available=_to_int(data.get("matches_available")),
            raw=data,
        )


@dataclass(frozen=True)
class MatchSummary:
    """A match summary row from list endpoints (league matches, today, picks)."""

    id: str
    kickoff: Optional[str] = None
    kickoff_local: Optional[str] = None
    league: Optional[League] = None
    home_team: Optional[str] = None
    away_team: Optional[str] = None
    probabilities: dict[str, Any] = field(default_factory=dict)
    confidence: dict[str, Any] = field(default_factory=dict)
    likely_scores: Optional[list[dict[str, Any]]] = None
    markets: dict[str, Any] = field(default_factory=dict)
    context: Optional[dict[str, Any]] = None
    status: Optional[str] = None
    result_score: Optional[str] = None
    pick: Optional[dict[str, Any]] = None
    availability: Optional[dict[str, Any]] = None
    raw: dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MatchSummary":
        league_data = data.get("league")
        return cls(
            id=str(data.get("id", "")),
            kickoff=data.get("kickoff"),
            kickoff_local=data.get("kickoff_local"),
            league=League.from_dict(league_data) if isinstance(league_data, dict) else None,
            home_team=data.get("home_team"),
            away_team=data.get("away_team"),
            probabilities=data.get("probabilities") or {},
            confidence=data.get("confidence") or {},
            likely_scores=data.get("likely_scores"),
            markets=data.get("markets") or {},
            context=data.get("context"),
            status=data.get("status"),
            result_score=data.get("result_score"),
            pick=data.get("pick"),
            availability=(
                data.get("availability") if isinstance(data.get("availability"), dict) else None
            ),
            raw=data,
        )


@dataclass(frozen=True)
class MatchDetail:
    """A full match payload from ``GET /v1/matches/{id}`` or the bulk endpoint.

    The Core Analytics payload is exposed through ``raw`` (and the section
    properties below). The SDK does not reimplement server-side analytics.
    """

    raw: dict[str, Any] = field(repr=False)

    @property
    def id(self) -> Optional[str]:
        match = self.raw.get("match")
        if isinstance(match, dict):
            return match.get("id")
        return self.raw.get("match_id")

    @property
    def kickoff(self) -> Optional[str]:
        match = self.raw.get("match")
        if isinstance(match, dict):
            return match.get("kickoff")
        return self.raw.get("kickoff")

    @property
    def competition_code(self) -> Optional[str]:
        match = self.raw.get("match")
        if isinstance(match, dict):
            competition = match.get("competition")
            if isinstance(competition, dict):
                return competition.get("id")
        return self.raw.get("competition_id")

    def _team_name(self, side: str) -> Optional[str]:
        match = self.raw.get("match")
        teams = match.get("teams") if isinstance(match, dict) else self.raw.get("teams")
        if isinstance(teams, dict):
            team = teams.get(side)
            if isinstance(team, dict):
                return team.get("name")
        return None

    @property
    def home_team(self) -> Optional[str]:
        return self._team_name("home")

    @property
    def away_team(self) -> Optional[str]:
        return self._team_name("away")

    @property
    def probabilities(self) -> Optional[dict[str, Any]]:
        return self.raw.get("probabilities")

    @property
    def forecast(self) -> Optional[dict[str, Any]]:
        return self.raw.get("forecast")

    @property
    def ratings(self) -> Optional[dict[str, Any]]:
        return self.raw.get("ratings")

    @property
    def statistics(self) -> Optional[dict[str, Any]]:
        return self.raw.get("statistics")

    @property
    def standings(self) -> Optional[dict[str, Any]]:
        return self.raw.get("standings")

    @property
    def availability(self) -> Optional[dict[str, Any]]:
        value = self.raw.get("availability")
        return value if isinstance(value, dict) else None

    def get(self, key: str, default: Any = None) -> Any:
        """Dict-style access to the raw payload."""

        return self.raw.get(key, default)


@dataclass(frozen=True)
class BulkItemError:
    """A per-match error entry from ``POST /v1/matches/bulk``."""

    match_id: str
    code: str
    raw: dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BulkItemError":
        return cls(
            match_id=str(data.get("match_id", "")),
            code=str(data.get("code", "")),
            raw=data,
        )


@dataclass(frozen=True)
class BulkResult:
    """The result of ``POST /v1/matches/bulk``: matches found plus per-ID errors.

    ``results`` preserves the order of the requested IDs (missing IDs are
    reported in ``errors`` and skipped in ``results``). ``errors`` is never
    hidden: check it to detect ``match_not_found`` entries.
    """

    results: list[MatchDetail]
    errors: list[BulkItemError]
    data_version: Optional[str] = None
    source: Optional[str] = None
    raw: dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BulkResult":
        return cls(
            results=[
                MatchDetail(raw=item)
                for item in data.get("results", [])
                if isinstance(item, dict)
            ],
            errors=[
                BulkItemError.from_dict(item)
                for item in data.get("errors", [])
                if isinstance(item, dict)
            ],
            data_version=data.get("data_version"),
            source=data.get("source"),
            raw=data,
        )


@dataclass(frozen=True)
class ApiResponse(Generic[T]):
    """A typed API response with its useful metadata.

    ``data`` holds the parsed result and is ``None`` only for ``304 Not
    Modified`` responses (when an ``etag`` argument was passed and the
    resource has not changed) — check :attr:`not_modified`.
    """

    data: Optional[T]
    payload: Optional[dict[str, Any]]
    etag: Optional[str]
    quota: Quota
    status_code: int

    @property
    def not_modified(self) -> bool:
        return self.status_code == 304

    @property
    def data_version(self) -> Optional[str]:
        if isinstance(self.payload, dict):
            return self.payload.get("data_version")
        return None

    @property
    def next_cursor(self) -> Optional[str]:
        if isinstance(self.payload, dict):
            value = self.payload.get("next_cursor")
            return str(value) if value else None
        return None

    @property
    def history_available_from(self) -> Optional[str]:
        if isinstance(self.payload, dict):
            value = self.payload.get("history_available_from")
            return str(value) if value else None
        return None

    @property
    def history_entitlement_days(self) -> Optional[int]:
        if isinstance(self.payload, dict):
            return _to_int(self.payload.get("history_entitlement_days"))
        return None
