# Foresportia Python SDK

[Documentation](https://qbarbedienne.github.io/foresportia-python/) ·
[API docs](https://www.foresportia.com/api/docs/)

[![PyPI version](https://img.shields.io/pypi/v/foresportia.svg)](https://pypi.org/project/foresportia/)
[![Python versions](https://img.shields.io/pypi/pyversions/foresportia.svg)](https://pypi.org/project/foresportia/)
[![License](https://img.shields.io/pypi/l/foresportia.svg)](https://pypi.org/project/foresportia/)
[![Package status](https://img.shields.io/pypi/status/foresportia.svg)](https://pypi.org/project/foresportia/)

Official Python SDK for the [Foresportia API](https://www.foresportia.com/api/docs/),
a football analytics API that provides match data, model probabilities,
predicted picks, confidence signals, and Core Analytics payloads for building
or enriching football prediction models.

The SDK targets server-side Python (3.9+) with a synchronous, typed client.

Public plans share the same SDK surface:

- **Developer — free:** 1 competition, up to 7 days of verified history,
  bulk requests up to 5 match IDs, and a limited analytics projection.
- **Starter — paid:** 20 competitions, up to 90 days of verified history,
  bulk requests up to 100 match IDs, and more complete analytics.
- **Legacy beta:** temporary compatibility for existing keys.

## Installation

```bash
pip install foresportia
```

Optional extras:

```bash
pip install "foresportia[ml]"    # numpy + scikit-learn for the ML example
pip install -e ".[dev]"          # local development from a clone
```

## Authentication and key safety

Authentication uses the `X-API-Key` header only. The SDK never puts the key in
a URL, and the key never appears in `repr()`, logs, or exception messages.

Store the key in an environment variable rather than in source code:

```bash
export FORES_API_KEY="fs_developer_your_key_here"
```

```powershell
$env:FORES_API_KEY = "fs_developer_your_key_here"
```

```python
from foresportia import ForesportiaClient

client = ForesportiaClient.from_env()          # reads FORES_API_KEY
# or explicitly:
client = ForesportiaClient(api_key="...", timeout=10.0)
```

The base URL must be HTTPS. Plain HTTP is only accepted for `localhost` or
with `allow_insecure_base_url=True` (development/testing only).

Do not commit API keys to source control, notebooks, screenshots, or support
tickets.

## Quickstart

```python
from foresportia import ForesportiaClient

with ForesportiaClient.from_env() as client:
    leagues = client.list_leagues()
    for league in leagues.data:
        print(league.code, league.name, league.matches_available)

    matches = client.list_league_matches(
        "PREMIER_LEAGUE",
        include="upcoming",
        start="2026-07-15",
        days=7,
    )
    for match in matches.data:
        print(match.kickoff, match.home_team, "vs", match.away_team, match.pick)
```

The SDK also accepts Starter and legacy beta keys without inferring a plan
from their prefix. The server remains authoritative for entitlements.

Every typed method returns an `ApiResponse` with:

```python
response.data           # typed result (list[League], list[MatchSummary], MatchDetail, BulkResult)
response.payload        # full JSON payload as a dict
response.etag           # ETag header for conditional requests
response.quota          # parsed rate-limit / quota headers
response.status_code    # HTTP status
response.not_modified   # True for 304 responses
```

## Available competitions

```python
leagues = client.list_leagues()
for league in leagues.data:
    print(league.code, league.name, league.country, league.activity_status)
```

Your API key only sees the competitions enabled for it. Use the codes exactly
as returned (for example in `list_league_matches`).

## Match detail

Match IDs from list endpoints look like `fsm:v1:<64 hex characters>`. Pass
them exactly as returned:

```python
match = client.get_match("fsm:v1:0123...abcdef")
detail = match.data
print(detail.home_team, "vs", detail.away_team)
print(detail.probabilities)   # 1X2, over/under, BTTS, draw no bet, ...
print(detail.ratings)         # ELO-style ratings
print(detail.raw)             # complete Core Analytics payload
```

## Bulk limits by plan

Developer accepts up to 5 match IDs per request; Starter accepts up to 100.
The SDK validates only the technical ceiling of 100. A Developer request with
more than 5 IDs is sent and the server returns `bulk_limit_exceeded`. Order is
preserved and per-ID failures do not hide successful results:

```python
bulk = client.get_matches_bulk([id_1, id_2, id_3])
for detail in bulk.data.results:
    print(detail.id, detail.home_team, "vs", detail.away_team)
for error in bulk.data.errors:
    print("failed:", error.match_id, error.code)   # e.g. match_not_found
```

## History and pagination

Developer provides up to 7 days of verified history and Starter up to 90 days.
Each request has a maximum window of 31 days. The effective archive may start
later at `response.history_available_from` while it fills progressively.

```python
page = client.list_league_matches("CHN", include="past", days=7, limit=50)
while True:
    for match in page.data:
        print(match.kickoff, match.home_team, match.away_team)
    if not page.next_cursor:
        break
    page = client.list_league_matches(
        "CHN", include="past", days=7, limit=50, cursor=page.next_cursor
    )

# Or stream rows without loading every page:
for match in client.iter_league_matches("CHN", include="past", days=7, limit=50):
    print(match.id)
```

The server may return `history_window_exceeded` when the requested dates fall
outside the key's entitlement.

## Today endpoints

```python
today = client.list_today_matches()
picks = client.list_today_picks(limit=20)
```

## Public health

`client.health()` returns the tolerant dictionary from the stable public
`GET /v1/health` endpoint. It reports service/data health and is not an
entitlement or account-status check. Unknown future fields are preserved.

## Quotas and rate limits

The API reports quota state in response headers; the SDK parses them into
`response.quota` (fields are `None` when the header is absent):

```python
response = client.list_leagues()
print(response.quota.remaining)                  # X-RateLimit-Remaining
print(response.quota.units_remaining_hour)       # X-Quota-Units-Remaining-Hour
print(response.quota.units_remaining_day)        # X-Quota-Units-Remaining-Day
print(response.quota.match_rows_remaining_day)   # X-Match-Rows-Remaining-Day
```

Quota enforcement stays server-side. On HTTP 429 the SDK raises
`ForesportiaRateLimitError` (or `ForesportiaConcurrencyLimitError`) carrying
`retry_after` and the quota snapshot. Retrying after 429 is opt-in:

```python
client = ForesportiaClient.from_env(retry_on_rate_limit=True, max_retries=2)
```

## ETags and conditional requests

Pass a previous `ETag` to skip unchanged payloads. A `304 Not Modified` is a
normal response, not an error:

```python
first = client.get_match(match_id)
second = client.get_match(match_id, etag=first.etag)
if second.not_modified:
    detail = first.data      # reuse the cached payload
else:
    detail = second.data
```

## Error handling

```python
from foresportia import (
    ForesportiaAuthenticationError,   # 401
    ForesportiaAuthorizationError,    # 403
    ForesportiaNotFoundError,         # 404
    ForesportiaValidationError,       # 400 / 422 / client-side validation
    ForesportiaRateLimitError,        # 429
    ForesportiaConcurrencyLimitError, # 429 concurrency_limit_exceeded
    ForesportiaServerError,           # 5xx
    ForesportiaTransportError,        # network / timeout
    ForesportiaAPIError,              # base class for all of the above
)

try:
    matches = client.list_today_matches()
except ForesportiaRateLimitError as exc:
    print("rate limited, retry after", exc.retry_after, "seconds")
except ForesportiaAPIError as exc:
    print(exc.status_code, exc.error_code, exc.endpoint)
```

Exceptions carry `status_code`, `error_code` (the API business code such as
`match_not_found` or `bulk_limit_exceeded`), `endpoint`, `retry_after`, and a
`quota` snapshot when available. The API key is never included.

Common business codes include `competition_not_selected`,
`history_window_exceeded`, and `bulk_limit_exceeded`. `starter_required` is
normally an `availability` value for a masked Developer field; if a future
endpoint returns it as an error code, it remains available through
`exception.error_code`. Unknown future codes use the same safe fallback.

## Retries and timeouts

- Explicit timeout per client (`timeout=10.0`, default 20 s).
- **Retries are disabled by default** (`max_retries=0`). A request that times
  out client-side may still have been processed and counted against your
  quota server-side, so each retry can consume an extra quota unit. Opt in
  explicitly when that trade-off is acceptable:

  ```python
  client = ForesportiaClient.from_env(max_retries=2)
  ```

  When enabled, only GET requests are retried, on network errors and
  502/503/504, with bounded exponential backoff.
- No automatic retry on 400/401/403/404, nor on 429 unless
  `retry_on_rate_limit=True`.
- The bulk POST is never retried on 5xx.
- Use the client as a context manager (`with ... as client:`) or call
  `client.close()`.

## Machine learning example

A runnable script is provided in
[examples/ml_starter_features.py](https://github.com/QBarbedienne/foresportia-python/blob/main/examples/ml_starter_features.py):
it fetches upcoming matches, extracts probabilities, markets, and confidence
into a feature matrix, and optionally fits a small scikit-learn model
(`pip install "foresportia[ml]"`). Foresportia outputs are model probabilities,
not guaranteed predictions; you need your own historical labels to train
anything meaningful.

```python
rows = []
for match in client.list_league_matches("PREMIER_LEAGUE", days=14).data:
    p = match.probabilities
    rows.append([p.get("home"), p.get("draw"), p.get("away"),
                 match.markets.get("btts"), match.confidence.get("score")])
```

## Legacy methods

The v0.1 dict-based methods keep working unchanged:

```python
client.me()
client.usage()
client.picks_today()
client.matches_today()
client.leagues()
client.league_matches("FIN", include="all", days=14, limit=10)
client.world_cup_2026_matches(limit=10)
```

Prefer the typed `list_*` / `get_*` methods for new code.

## Links

- API documentation: https://www.foresportia.com/api/docs/
- LLM-friendly API reference: https://www.foresportia.com/api/docs/llms-full.txt
- Homepage: https://www.foresportia.com
- Developer docs (EN): https://www.foresportia.com/en/developers.html
- API dashboard (EN): https://www.foresportia.com/en/api-dashboard.html
- Repository: https://github.com/QBarbedienne/foresportia-python
- Issues: https://github.com/QBarbedienne/foresportia-python/issues

## Disclaimer

Foresportia provides football probabilities, model outputs, and analytics
data. It does not provide betting advice, financial advice, bookmaker odds,
guaranteed outcomes, or instructions to place wagers. Any use of Foresportia
data is the responsibility of the user and should comply with applicable laws,
regulations, and platform policies.

## License

MIT. See
[LICENSE](https://github.com/QBarbedienne/foresportia-python/blob/main/LICENSE).
