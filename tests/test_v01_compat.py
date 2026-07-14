"""Explicit backward-compatibility tests for the v0.1.0 public surface.

Every method that existed in 0.1.0 must keep returning a plain ``dict``
(never ``ApiResponse``), with the same payload shape, so historical user
code keeps working unchanged.
"""

import respx
from httpx import Response

from foresportia import ApiResponse, ForesportiaClient

BASE_URL = "https://api.foresportia.com"
API_KEY = "fs_beta_test_key"

ME_PAYLOAD = {"status": "active", "plan": "starter", "client": {}, "endpoints": []}
USAGE_PAYLOAD = {"daily": {"used": 1}, "monthly": {}, "rate_limit_minute": {}, "last_used_at": None}
MATCHES_PAYLOAD = {
    "date": "2026-07-14",
    "timezone": "Europe/Paris",
    "source": "Foresportia",
    "data_version": "v",
    "matches": [{"id": "fsm:v1:" + "a" * 64, "home_team": "A", "away_team": "B"}],
}
LEAGUES_PAYLOAD = {
    "source": "Foresportia",
    "data_version": "v",
    "leagues": [{"code": "FIN", "name": "Veikkausliiga"}],
}


def _client() -> ForesportiaClient:
    return ForesportiaClient(API_KEY)


@respx.mock
def test_me_returns_plain_dict():
    respx.get(f"{BASE_URL}/v1/me").mock(return_value=Response(200, json=ME_PAYLOAD))
    with _client() as client:
        result = client.me()
    assert type(result) is dict
    assert not isinstance(result, ApiResponse)
    assert result["plan"] == "starter"


@respx.mock
def test_usage_returns_plain_dict():
    respx.get(f"{BASE_URL}/v1/me/usage").mock(return_value=Response(200, json=USAGE_PAYLOAD))
    with _client() as client:
        result = client.usage()
    assert type(result) is dict
    assert result["daily"]["used"] == 1


@respx.mock
def test_picks_today_returns_plain_dict():
    respx.get(f"{BASE_URL}/v1/picks/today").mock(return_value=Response(200, json=MATCHES_PAYLOAD))
    with _client() as client:
        result = client.picks_today()
    assert type(result) is dict
    # Historical dict-style access patterns keep working.
    assert result["matches"][0]["home_team"] == "A"
    assert result.get("date") == "2026-07-14"


@respx.mock
def test_matches_today_returns_plain_dict():
    respx.get(f"{BASE_URL}/v1/matches/today").mock(return_value=Response(200, json=MATCHES_PAYLOAD))
    with _client() as client:
        result = client.matches_today()
    assert type(result) is dict
    assert len(result["matches"]) == 1


@respx.mock
def test_leagues_returns_plain_dict():
    respx.get(f"{BASE_URL}/v1/leagues").mock(return_value=Response(200, json=LEAGUES_PAYLOAD))
    with _client() as client:
        result = client.leagues()
    assert type(result) is dict
    assert result["leagues"][0]["code"] == "FIN"


@respx.mock
def test_league_matches_returns_plain_dict_with_v01_defaults():
    route = respx.get(f"{BASE_URL}/v1/leagues/FIN/matches").mock(
        return_value=Response(200, json=MATCHES_PAYLOAD)
    )
    with _client() as client:
        result = client.league_matches("FIN")
    assert type(result) is dict
    assert result["matches"][0]["id"].startswith("fsm:v1:")
    # v0.1.0 default query parameters are preserved.
    params = route.calls.last.request.url.params
    assert params["include"] == "upcoming"
    assert params["days"] == "31"
    assert params["limit"] == "100"


@respx.mock
def test_league_matches_accepts_v01_positional_arguments():
    route = respx.get(f"{BASE_URL}/v1/leagues/FIN/matches").mock(
        return_value=Response(200, json=MATCHES_PAYLOAD)
    )
    with _client() as client:
        result = client.league_matches("FIN", "all", 14, 10, "2026-07-15")
    assert type(result) is dict
    params = route.calls.last.request.url.params
    assert params["include"] == "all"
    assert params["days"] == "14"
    assert params["limit"] == "10"
    assert params["start"] == "2026-07-15"


@respx.mock
def test_world_cup_2026_matches_returns_plain_dict():
    route = respx.get(f"{BASE_URL}/v1/leagues/WORLD_CUP_2026/matches").mock(
        return_value=Response(200, json=MATCHES_PAYLOAD)
    )
    with _client() as client:
        result = client.world_cup_2026_matches(limit=10)
    assert type(result) is dict
    assert route.calls.last.request.url.params["include"] == "all"


def test_v01_public_surface_is_intact():
    expected = {
        "me",
        "usage",
        "picks_today",
        "matches_today",
        "leagues",
        "league_matches",
        "world_cup_2026_matches",
        "from_env",
        "close",
        "__enter__",
        "__exit__",
    }
    missing = {name for name in expected if not callable(getattr(ForesportiaClient, name, None))}
    assert not missing, f"v0.1.0 methods missing: {missing}"


@respx.mock
def test_retries_are_disabled_by_default():
    route = respx.get(f"{BASE_URL}/v1/leagues").mock(return_value=Response(503, text="down"))
    with _client() as client:
        try:
            client.leagues()
        except Exception:
            pass
    assert route.call_count == 1
