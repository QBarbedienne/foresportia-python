import pytest
import respx
from httpx import Response

from foresportia import (
    ForesportiaAPIError,
    ForesportiaAuthError,
    ForesportiaClient,
    ForesportiaConfigurationError,
    ForesportiaRateLimitError,
)


BASE_URL = "https://api.foresportia.com"


def test_from_env_reads_api_key(monkeypatch):
    monkeypatch.setenv("FORES_API_KEY", "fs_beta_test_key")

    with ForesportiaClient.from_env() as client:
        assert client._client.headers["X-API-Key"] == "fs_beta_test_key"


def test_from_env_without_variable_raises(monkeypatch):
    monkeypatch.delenv("FORES_API_KEY", raising=False)

    with pytest.raises(ForesportiaConfigurationError):
        ForesportiaClient.from_env()


@respx.mock
def test_me_calls_me_endpoint():
    route = respx.get(f"{BASE_URL}/v1/me").mock(return_value=Response(200, json={"id": "acct"}))

    with ForesportiaClient("fs_beta_test_key") as client:
        assert client.me() == {"id": "acct"}

    assert route.called


@respx.mock
def test_league_matches_builds_query_params():
    route = respx.get(f"{BASE_URL}/v1/leagues/CHN/matches").mock(
        return_value=Response(200, json={"matches": []})
    )

    with ForesportiaClient("fs_beta_test_key") as client:
        client.league_matches("CHN", include="all", days=14, limit=10)

    request = route.calls.last.request
    assert request.url.params["include"] == "all"
    assert request.url.params["days"] == "14"
    assert request.url.params["limit"] == "10"


@respx.mock
def test_world_cup_2026_matches_uses_world_cup_code():
    route = respx.get(f"{BASE_URL}/v1/leagues/WORLD_CUP_2026/matches").mock(
        return_value=Response(200, json={"matches": []})
    )

    with ForesportiaClient("fs_beta_test_key") as client:
        client.world_cup_2026_matches(limit=10)

    assert route.called
    assert route.calls.last.request.url.params["include"] == "all"
    assert route.calls.last.request.url.params["limit"] == "10"


@respx.mock
def test_x_api_key_header_is_present():
    route = respx.get(f"{BASE_URL}/v1/me").mock(return_value=Response(200, json={"ok": True}))

    with ForesportiaClient("fs_beta_test_key") as client:
        client.me()

    assert route.calls.last.request.headers["X-API-Key"] == "fs_beta_test_key"


@respx.mock
def test_api_key_is_absent_from_url():
    route = respx.get(f"{BASE_URL}/v1/me").mock(return_value=Response(200, json={"ok": True}))

    with ForesportiaClient("fs_beta_test_key") as client:
        client.me()

    assert "fs_beta_test_key" not in str(route.calls.last.request.url)


@respx.mock
def test_401_raises_auth_error():
    respx.get(f"{BASE_URL}/v1/me").mock(return_value=Response(401, text="Unauthorized"))

    with ForesportiaClient("fs_beta_test_key") as client:
        with pytest.raises(ForesportiaAuthError) as exc_info:
            client.me()

    assert exc_info.value.status_code == 401
    assert exc_info.value.endpoint == "/v1/me"


@respx.mock
def test_429_raises_rate_limit_error():
    respx.get(f"{BASE_URL}/v1/me").mock(return_value=Response(429, text="Too many requests"))

    with ForesportiaClient("fs_beta_test_key") as client:
        with pytest.raises(ForesportiaRateLimitError) as exc_info:
            client.me()

    assert exc_info.value.status_code == 429
    assert exc_info.value.endpoint == "/v1/me"


@respx.mock
def test_500_raises_api_error():
    respx.get(f"{BASE_URL}/v1/me").mock(return_value=Response(500, text="Server error"))

    with ForesportiaClient("fs_beta_test_key") as client:
        with pytest.raises(ForesportiaAPIError) as exc_info:
            client.me()

    assert exc_info.value.status_code == 500
    assert exc_info.value.response_text == "Server error"
    assert exc_info.value.endpoint == "/v1/me"


@respx.mock
def test_invalid_json_raises_api_error():
    respx.get(f"{BASE_URL}/v1/me").mock(return_value=Response(200, text="not json"))

    with ForesportiaClient("fs_beta_test_key") as client:
        with pytest.raises(ForesportiaAPIError) as exc_info:
            client.me()

    assert exc_info.value.status_code == 200
    assert exc_info.value.response_text == "not json"
    assert exc_info.value.endpoint == "/v1/me"
