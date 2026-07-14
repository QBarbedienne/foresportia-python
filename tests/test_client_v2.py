"""Tests for the typed v0.2 client API (mocked HTTP, no production calls)."""

import httpx
import pytest
import respx
from httpx import Response

from foresportia import (
    ForesportiaAuthenticationError,
    ForesportiaAuthorizationError,
    ForesportiaClient,
    ForesportiaConcurrencyLimitError,
    ForesportiaConfigurationError,
    ForesportiaNotFoundError,
    ForesportiaRateLimitError,
    ForesportiaServerError,
    ForesportiaTransportError,
    ForesportiaValidationError,
)

BASE_URL = "https://api.foresportia.com"
API_KEY = "fs_beta_test_key"
HEX_ID_1 = "fsm:v1:" + "a" * 64
HEX_ID_2 = "fsm:v1:" + "b" * 64

QUOTA_HEADERS = {
    "X-RateLimit-Limit": "15",
    "X-RateLimit-Remaining": "14",
    "X-RateLimit-Reset": "1760000000",
    "X-Quota-Units-Remaining-Hour": "499",
    "X-Quota-Units-Remaining-Day": "2999",
    "X-Match-Rows-Remaining-Day": "9999",
}

MATCH_SUMMARY = {
    "id": HEX_ID_1,
    "kickoff": "2026-07-15T19:00:00Z",
    "kickoff_local": "2026-07-15T21:00:00+02:00",
    "league": {"code": "PREMIER_LEAGUE", "name": "Premier League", "country": "England"},
    "home_team": "Arsenal",
    "away_team": "Chelsea",
    "probabilities": {"home": 0.5, "draw": 0.3, "away": 0.2},
    "confidence": {"score": 0.7},
    "likely_scores": [{"score": "2-1", "probability": 0.11}],
    "markets": {"btts": 0.55},
    "status": "scheduled",
    "result_score": None,
    "pick": {"outcome": "home", "probability": 0.5},
}


def _client(**kwargs):
    kwargs.setdefault("max_retries", 0)
    return ForesportiaClient(API_KEY, **kwargs)


# --------------------------------------------------------------------- #
# Configuration and security                                             #
# --------------------------------------------------------------------- #


def test_http_base_url_is_rejected_by_default():
    with pytest.raises(ForesportiaConfigurationError):
        ForesportiaClient(API_KEY, base_url="http://api.example.com")


def test_http_localhost_base_url_is_allowed():
    with ForesportiaClient(API_KEY, base_url="http://localhost:8000") as client:
        assert client.base_url == "http://localhost:8000"


def test_http_base_url_allowed_with_explicit_flag():
    client = ForesportiaClient(
        API_KEY, base_url="http://staging.internal", allow_insecure_base_url=True
    )
    client.close()


def test_repr_does_not_contain_api_key():
    with _client() as client:
        assert API_KEY not in repr(client)


def test_negative_max_retries_rejected():
    with pytest.raises(ForesportiaConfigurationError):
        ForesportiaClient(API_KEY, max_retries=-1)


@respx.mock
def test_api_key_absent_from_exception_on_error():
    respx.get(f"{BASE_URL}/v1/leagues").mock(return_value=Response(500, text="boom"))
    with _client() as client:
        with pytest.raises(ForesportiaServerError) as exc_info:
            client.list_leagues()
    blob = repr(exc_info.value) + str(exc_info.value) + repr(vars(exc_info.value))
    assert API_KEY not in blob


# --------------------------------------------------------------------- #
# Leagues                                                                #
# --------------------------------------------------------------------- #


@respx.mock
def test_list_leagues_parses_typed_rows_and_metadata():
    respx.get(f"{BASE_URL}/v1/leagues").mock(
        return_value=Response(
            200,
            json={
                "source": "Foresportia",
                "data_version": "release-42",
                "leagues": [
                    {
                        "code": "PREMIER_LEAGUE",
                        "name": "Premier League",
                        "country": "England",
                        "catalog_status": "selectable",
                        "activity_status": "active",
                        "available": True,
                        "matches_available": 10,
                    }
                ],
            },
            headers={"ETag": '"abc"', **QUOTA_HEADERS},
        )
    )
    with _client() as client:
        response = client.list_leagues()

    assert response.status_code == 200
    assert response.etag == '"abc"'
    assert response.data_version == "release-42"
    league = response.data[0]
    assert league.code == "PREMIER_LEAGUE"
    assert league.matches_available == 10
    assert response.quota.limit == 15
    assert response.quota.units_remaining_hour == 499
    assert response.quota.match_rows_remaining_day == 9999


@respx.mock
def test_list_leagues_tolerates_unknown_fields():
    respx.get(f"{BASE_URL}/v1/leagues").mock(
        return_value=Response(
            200,
            json={
                "data_version": "v",
                "leagues": [{"code": "FIN", "brand_new_field": {"x": 1}}],
                "another_new_top_level": True,
            },
        )
    )
    with _client() as client:
        response = client.list_leagues()
    assert response.data[0].code == "FIN"
    assert response.data[0].raw["brand_new_field"] == {"x": 1}


# --------------------------------------------------------------------- #
# League matches                                                         #
# --------------------------------------------------------------------- #


@respx.mock
def test_list_league_matches_sends_expected_params():
    route = respx.get(f"{BASE_URL}/v1/leagues/PREMIER_LEAGUE/matches").mock(
        return_value=Response(200, json={"matches": [MATCH_SUMMARY]})
    )
    with _client() as client:
        response = client.list_league_matches(
            "PREMIER_LEAGUE", start="2026-07-15", days=7, limit=50, include="all"
        )

    params = route.calls.last.request.url.params
    assert params["include"] == "all"
    assert params["start"] == "2026-07-15"
    assert params["days"] == "7"
    assert params["limit"] == "50"
    match = response.data[0]
    assert match.home_team == "Arsenal"
    assert match.league.code == "PREMIER_LEAGUE"
    assert match.pick == {"outcome": "home", "probability": 0.5}


@respx.mock
def test_list_league_matches_accepts_date_object():
    import datetime

    route = respx.get(f"{BASE_URL}/v1/leagues/FIN/matches").mock(
        return_value=Response(200, json={"matches": []})
    )
    with _client() as client:
        client.list_league_matches("FIN", start=datetime.date(2026, 7, 15))
    assert route.calls.last.request.url.params["start"] == "2026-07-15"


def test_list_league_matches_rejects_empty_code():
    with _client() as client:
        with pytest.raises(ForesportiaValidationError):
            client.list_league_matches("  ")


# --------------------------------------------------------------------- #
# Match detail and ETag / 304                                            #
# --------------------------------------------------------------------- #


@respx.mock
def test_get_match_returns_detail_wrapper():
    payload = {
        "schema_version": "starter.v1",
        "match": {
            "id": HEX_ID_1,
            "kickoff": "2026-07-15T19:00:00Z",
            "competition": {"id": "PREMIER_LEAGUE", "name": "Premier League"},
            "teams": {"home": {"name": "Arsenal"}, "away": {"name": "Chelsea"}},
        },
        "probabilities": {"one_x_two": {"home": 0.5, "draw": 0.3, "away": 0.2}},
    }
    respx.get(f"{BASE_URL}/v1/matches/{HEX_ID_1}").mock(
        return_value=Response(200, json=payload, headers={"ETag": '"m1"'})
    )
    with _client() as client:
        response = client.get_match(HEX_ID_1)

    detail = response.data
    assert detail.id == HEX_ID_1
    assert detail.home_team == "Arsenal"
    assert detail.competition_code == "PREMIER_LEAGUE"
    assert detail.probabilities["one_x_two"]["home"] == 0.5
    assert detail.raw == payload
    assert response.etag == '"m1"'


@respx.mock
def test_get_match_does_not_rewrite_id():
    route = respx.get(f"{BASE_URL}/v1/matches/{HEX_ID_1}").mock(
        return_value=Response(200, json={"match": {"id": HEX_ID_1}})
    )
    with _client() as client:
        client.get_match(HEX_ID_1)
    assert HEX_ID_1 in str(route.calls.last.request.url)
    assert "fixture:" not in str(route.calls.last.request.url)


@respx.mock
def test_get_match_etag_sends_if_none_match_and_304_is_not_an_error():
    route = respx.get(f"{BASE_URL}/v1/matches/{HEX_ID_1}").mock(
        return_value=Response(304, headers={"ETag": '"m1"', **QUOTA_HEADERS})
    )
    with _client() as client:
        response = client.get_match(HEX_ID_1, etag='"m1"')

    assert route.calls.last.request.headers["If-None-Match"] == '"m1"'
    assert response.not_modified is True
    assert response.status_code == 304
    assert response.data is None
    assert response.etag == '"m1"'
    assert response.quota.units_remaining_hour == 499


@respx.mock
def test_get_match_404_raises_not_found():
    respx.get(f"{BASE_URL}/v1/matches/{HEX_ID_1}").mock(
        return_value=Response(404, json={"detail": "match_not_found"})
    )
    with _client() as client:
        with pytest.raises(ForesportiaNotFoundError) as exc_info:
            client.get_match(HEX_ID_1)
    assert exc_info.value.status_code == 404
    assert exc_info.value.error_code == "match_not_found"


# --------------------------------------------------------------------- #
# Bulk                                                                   #
# --------------------------------------------------------------------- #


@respx.mock
def test_bulk_posts_ids_and_exposes_partial_errors():
    route = respx.post(f"{BASE_URL}/v1/matches/bulk").mock(
        return_value=Response(
            200,
            json={
                "source": "Foresportia",
                "data_version": "release-42",
                "results": [{"match": {"id": HEX_ID_1}}],
                "errors": [{"match_id": HEX_ID_2, "code": "match_not_found"}],
            },
            headers=QUOTA_HEADERS,
        )
    )
    with _client() as client:
        response = client.get_matches_bulk([HEX_ID_1, HEX_ID_2])

    import json

    body = json.loads(route.calls.last.request.content)
    assert body == {"match_ids": [HEX_ID_1, HEX_ID_2]}

    bulk = response.data
    assert bulk.results[0].id == HEX_ID_1
    assert bulk.errors[0].match_id == HEX_ID_2
    assert bulk.errors[0].code == "match_not_found"
    assert bulk.data_version == "release-42"
    assert response.quota.match_rows_remaining_day == 9999


def test_bulk_rejects_empty_list_client_side():
    with _client() as client:
        with pytest.raises(ForesportiaValidationError):
            client.get_matches_bulk([])


def test_bulk_rejects_more_than_100_ids_client_side():
    ids = ["fsm:v1:" + f"{index:064x}" for index in range(101)]
    with _client() as client:
        with pytest.raises(ForesportiaValidationError):
            client.get_matches_bulk(ids)


def test_bulk_rejects_duplicates_client_side():
    with _client() as client:
        with pytest.raises(ForesportiaValidationError) as exc_info:
            client.get_matches_bulk([HEX_ID_1, HEX_ID_1])
    assert "duplicate" in str(exc_info.value).lower()


def test_bulk_rejects_invalid_id_format_client_side():
    with _client() as client:
        with pytest.raises(ForesportiaValidationError):
            client.get_matches_bulk(["fixture:123"])
        with pytest.raises(ForesportiaValidationError):
            client.get_matches_bulk(["fsm:v1:" + "Z" * 64])


@respx.mock
def test_bulk_is_not_retried_on_5xx():
    route = respx.post(f"{BASE_URL}/v1/matches/bulk").mock(
        return_value=Response(503, text="unavailable")
    )
    with ForesportiaClient(API_KEY, max_retries=3) as client:
        with pytest.raises(ForesportiaServerError):
            client.get_matches_bulk([HEX_ID_1])
    assert route.call_count == 1


# --------------------------------------------------------------------- #
# Today endpoints                                                        #
# --------------------------------------------------------------------- #


@respx.mock
def test_list_today_matches_and_picks():
    respx.get(f"{BASE_URL}/v1/matches/today").mock(
        return_value=Response(200, json={"date": "2026-07-14", "matches": [MATCH_SUMMARY]})
    )
    picks_route = respx.get(f"{BASE_URL}/v1/picks/today").mock(
        return_value=Response(200, json={"date": "2026-07-14", "matches": [MATCH_SUMMARY]})
    )
    with _client() as client:
        today = client.list_today_matches()
        picks = client.list_today_picks(limit=5)

    assert today.data[0].id == HEX_ID_1
    assert picks.data[0].away_team == "Chelsea"
    assert picks_route.calls.last.request.url.params["limit"] == "5"


# --------------------------------------------------------------------- #
# Error mapping                                                          #
# --------------------------------------------------------------------- #


@respx.mock
@pytest.mark.parametrize(
    ("status", "detail", "exc_type"),
    [
        (400, "invalid_match_id", ForesportiaValidationError),
        (401, "Invalid API key", ForesportiaAuthenticationError),
        (403, "bulk_not_available", ForesportiaAuthorizationError),
        (404, "match_not_found", ForesportiaNotFoundError),
        (422, "validation error", ForesportiaValidationError),
        (429, "rate_limit_exceeded", ForesportiaRateLimitError),
        (500, "boom", ForesportiaServerError),
        (503, "down", ForesportiaServerError),
    ],
)
def test_status_codes_map_to_typed_exceptions(status, detail, exc_type):
    respx.get(f"{BASE_URL}/v1/leagues").mock(
        return_value=Response(status, json={"detail": detail})
    )
    with _client() as client:
        with pytest.raises(exc_type) as exc_info:
            client.list_leagues()
    assert exc_info.value.status_code == status
    assert exc_info.value.error_code == detail


@respx.mock
def test_429_exposes_retry_after_and_quota():
    respx.get(f"{BASE_URL}/v1/leagues").mock(
        return_value=Response(
            429,
            json={"detail": "rate_limit_exceeded"},
            headers={"Retry-After": "60", **QUOTA_HEADERS},
        )
    )
    with _client() as client:
        with pytest.raises(ForesportiaRateLimitError) as exc_info:
            client.list_leagues()
    assert exc_info.value.retry_after == 60
    assert exc_info.value.quota.units_remaining_hour == 499


@respx.mock
def test_429_concurrency_code_raises_concurrency_error():
    respx.get(f"{BASE_URL}/v1/leagues").mock(
        return_value=Response(
            429,
            json={"detail": "concurrency_limit_exceeded"},
            headers={"Retry-After": "1"},
        )
    )
    with _client() as client:
        with pytest.raises(ForesportiaConcurrencyLimitError) as exc_info:
            client.list_leagues()
    assert exc_info.value.retry_after == 1
    assert isinstance(exc_info.value, ForesportiaRateLimitError)


@respx.mock
def test_timeout_raises_transport_error():
    respx.get(f"{BASE_URL}/v1/leagues").mock(side_effect=httpx.ReadTimeout("timed out"))
    with _client() as client:
        with pytest.raises(ForesportiaTransportError):
            client.list_leagues()


# --------------------------------------------------------------------- #
# Retries                                                                #
# --------------------------------------------------------------------- #


@respx.mock
def test_get_retries_on_503_then_succeeds(monkeypatch):
    monkeypatch.setattr("foresportia.client.time.sleep", lambda _s: None)
    route = respx.get(f"{BASE_URL}/v1/leagues")
    route.side_effect = [
        Response(503, text="down"),
        Response(200, json={"leagues": []}),
    ]
    with ForesportiaClient(API_KEY, max_retries=2) as client:
        response = client.list_leagues()
    assert response.status_code == 200
    assert route.call_count == 2


@respx.mock
def test_get_retries_on_network_error(monkeypatch):
    monkeypatch.setattr("foresportia.client.time.sleep", lambda _s: None)
    route = respx.get(f"{BASE_URL}/v1/leagues")
    route.side_effect = [
        httpx.ConnectError("refused"),
        Response(200, json={"leagues": []}),
    ]
    with ForesportiaClient(API_KEY, max_retries=1) as client:
        response = client.list_leagues()
    assert response.status_code == 200
    assert route.call_count == 2


@respx.mock
def test_no_retry_when_disabled():
    route = respx.get(f"{BASE_URL}/v1/leagues").mock(return_value=Response(503, text="down"))
    with _client() as client:
        with pytest.raises(ForesportiaServerError):
            client.list_leagues()
    assert route.call_count == 1


@respx.mock
def test_429_not_retried_by_default():
    route = respx.get(f"{BASE_URL}/v1/leagues").mock(
        return_value=Response(429, json={"detail": "rate_limit_exceeded"})
    )
    with ForesportiaClient(API_KEY, max_retries=3) as client:
        with pytest.raises(ForesportiaRateLimitError):
            client.list_leagues()
    assert route.call_count == 1


@respx.mock
def test_429_retried_when_explicitly_enabled(monkeypatch):
    monkeypatch.setattr("foresportia.client.time.sleep", lambda _s: None)
    route = respx.get(f"{BASE_URL}/v1/leagues")
    route.side_effect = [
        Response(429, json={"detail": "rate_limit_exceeded"}, headers={"Retry-After": "1"}),
        Response(200, json={"leagues": []}),
    ]
    with ForesportiaClient(API_KEY, max_retries=1, retry_on_rate_limit=True) as client:
        response = client.list_leagues()
    assert response.status_code == 200
    assert route.call_count == 2


@respx.mock
def test_401_never_retried():
    route = respx.get(f"{BASE_URL}/v1/leagues").mock(
        return_value=Response(401, json={"detail": "Invalid API key"})
    )
    with ForesportiaClient(API_KEY, max_retries=3) as client:
        with pytest.raises(ForesportiaAuthenticationError):
            client.list_leagues()
    assert route.call_count == 1


# --------------------------------------------------------------------- #
# Legacy compatibility                                                   #
# --------------------------------------------------------------------- #


@respx.mock
def test_legacy_methods_still_return_dicts():
    respx.get(f"{BASE_URL}/v1/me").mock(return_value=Response(200, json={"plan": "starter"}))
    respx.get(f"{BASE_URL}/v1/picks/today").mock(
        return_value=Response(200, json={"matches": []})
    )
    with _client() as client:
        assert client.me() == {"plan": "starter"}
        assert client.picks_today() == {"matches": []}
