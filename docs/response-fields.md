# Response Fields

Since version 0.2.0 the typed methods (`list_leagues`, `list_league_matches`,
`get_match`, `get_matches_bulk`, `list_today_matches`, `list_today_picks`)
return an `ApiResponse` whose `data` holds lightweight typed models. The
models are tolerant by design: they expose common fields with types while
keeping the complete server payload in `.raw`, so new optional fields added by
the API never break parsing.

The 0.1.0 dict-based methods (`picks_today()`, `leagues()`, ...) keep
returning raw dictionaries.

## ApiResponse

```python
response = client.list_leagues()

response.data           # typed result
response.payload        # full JSON payload as a dict
response.etag           # ETag header value
response.quota          # parsed quota headers (see below)
response.status_code    # HTTP status
response.not_modified   # True for 304 responses (conditional requests)
response.data_version   # dataset release identifier when present
response.next_cursor    # opaque league-match continuation cursor
response.history_available_from
response.history_entitlement_days
```

## League

From `list_leagues()`:

- `code` — competition code to use in other calls (e.g. `PREMIER_LEAGUE`).
- `name`, `country`.
- `catalog_status`, `activity_status`, `available`, `matches_available`.
- `raw` — the full row.

## MatchSummary

From `list_league_matches()`, `list_today_matches()`, `list_today_picks()`:

- `id` — public match identifier (`fsm:v1:<64 hex characters>`). Pass it
  unchanged to `get_match()` and `get_matches_bulk()`.
- `kickoff` (UTC) and `kickoff_local`.
- `league` — a `League` with `code`, `name`, `country`.
- `home_team`, `away_team`.
- `probabilities` — dict with `home`, `draw`, `away`.
- `confidence` — dict with `score` when available.
- `likely_scores` — list of `{"score": "2-1", "probability": ...}` entries.
- `markets` — dict with fields such as `btts`, `over_2_5`, `under_2_5`,
  `dnb_home`, `dnb_away`, `double_chance_1x`, `double_chance_x2`,
  `double_chance_12`.
- `status`, `result_score`, `pick` (`{"outcome": ..., "probability": ...}`),
  `context`.
- `availability` — tolerant map explaining selected fields not present in this
  summary projection when supplied by the endpoint.
- `raw` — the full row.

## MatchDetail

From `get_match()` and bulk results — the Core Analytics payload. Convenience
properties: `id`, `kickoff`, `competition_code`, `home_team`, `away_team`,
`probabilities`, `forecast`, `ratings`, `statistics`, `standings`, and
`availability`. The
complete payload is in `.raw` (also reachable via `.get("section")`).

Section availability depends on your plan; see the
[official API reference](https://www.foresportia.com/api/docs/) for the
payload contract.

For Developer, selected fields can be reserved for Starter without causing an
SDK error:

```python
if match.availability:
    elo_status = match.availability.get("ratings.elo_home")
    if elo_status == "starter_required":
        print("This field is available on Starter")
```

The map may be absent, `null`, partial, or contain future keys and detailed
objects. List payloads do not promise every analytical field present in match
detail.

## BulkResult

From `get_matches_bulk()`:

- `results` — list of `MatchDetail`, in request order (missing IDs skipped).
- `errors` — list of `BulkItemError` with `match_id` and `code`
  (e.g. `match_not_found`). Errors are reported, never hidden.
- `data_version`, `source`, `raw`.

## Quota

Parsed from response headers; every field is `None` when the header is absent:

- `limit`, `remaining`, `reset_at` — `X-RateLimit-*`.
- `units_remaining_hour`, `units_remaining_day` — `X-Quota-Units-Remaining-*`.
- `match_rows_remaining_day` — `X-Match-Rows-Remaining-Day`.
- `retry_after` — `Retry-After` (on 429).

## Optional Fields and Missing Values

A field may be missing because the endpoint does not include it, the match is
outside available coverage, or the model output is not published yet. Typed
model fields default to `None` (or empty dicts) in that case, and unknown new
fields remain accessible through `.raw`:

```python
match = response.data[0]
probability = match.probabilities.get("home")   # None-safe
extra = match.raw.get("some_future_field")
```

Avoid assuming that every match has probabilities, confidence, or likely
scores. Probabilities are model outputs, not guarantees.
