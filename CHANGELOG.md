# Changelog

All notable changes to the Foresportia Python SDK will be documented in this
file.

## 0.3.1 - 2026-07-23

### Added

- `ForesportiaClient.list_league_history()` and `iter_league_history()`: thin
  wrappers over `list_league_matches()` / `iter_league_matches()` that always
  request `include="past"`, with identical parameters, return types, metadata,
  and typed errors (no new route or HTTP path).
- `MatchSummary.is_final` (mirrors `status == "final"`) and
  `MatchSummary.predicted_outcome` (the published `pick["outcome"]` as
  `Literal["home", "draw", "away"] | None`, never recomputed from probabilities).

### Changed

- `list_league_history()` / `iter_league_history()` now default `days=None`.
  When `days` is `None` the parameter is omitted from the request, so the
  server resolves the window from the key's real history entitlement (capped at
  31 days per request); an explicit `days` is forwarded unchanged. The SDK does
  not resolve the entitlement locally and makes no extra plan-discovery call.
- `list_league_matches()` / `iter_league_matches()` now accept `days=None` to
  omit the parameter. Their public default value stays `14`, so existing calls
  are unaffected.

### Compatibility

- No existing method signature default value or return type changed (the `days`
  parameter type is widened to accept `None`). The package version is unchanged;
  these additions are expected to ship in a future `0.3.1`.

### Notes

- The automatic-window resolution (`include=past` + `days` absent →
  `min(history_entitlement_days, 31)`) is applied by the API server. `include=all`
  and `include=upcoming` keep their existing default-window behaviour.

## 0.3.0 - 2026-07-16

### Added

- Cursor pagination support through `list_league_matches(cursor=...)` and the
  lazy `iter_league_matches()` helper.
- `ApiResponse.next_cursor`, `history_available_from`, and
  `history_entitlement_days` metadata.
- Tolerant `availability` access on `MatchSummary` and `MatchDetail`.
- A tolerant `health()` wrapper for the stable public `GET /v1/health` route.
- Public Developer plan documentation and `examples/developer_quickstart.py`.

### Changed

- Bulk documentation is now plan-aware: Developer accepts up to 5 match IDs,
  Starter up to 100, and the server remains authoritative.
- History documentation now distinguishes Developer (7 days) and Starter
  (90 days), while retaining the 31-day maximum request window.
- Beta wording now refers only to temporary legacy access.

### Compatibility

- No existing client method signature or return type was broken.
- Existing beta keys remain accepted; the SDK does not infer plans from key
  prefixes.
- The 0.1.0 dict-based and 0.2.0 typed APIs remain available.

## 0.2.0 - 2026-07-14

- Added typed methods aligned with the current public API surface:
  `list_leagues()`, `list_league_matches()`, `get_match()`,
  `get_matches_bulk()`, `list_today_matches()`, `list_today_picks()`.
- Added `ApiResponse` exposing `data`, `payload`, `etag`, `quota`,
  `status_code`, and `not_modified`.
- Added lightweight tolerant models: `League`, `MatchSummary`, `MatchDetail`,
  `BulkResult`, `BulkItemError`, `Quota`.
- Added support for `POST /v1/matches/bulk` (Starter plan) with client-side
  validation (1–100 unique `fsm:v1:<64hex>` IDs) and partial-error reporting.
- Added ETag / `If-None-Match` conditional requests; `304 Not Modified` is a
  normal response (`response.not_modified`), never a generic error.
- Added quota header parsing (`X-RateLimit-*`, `X-Quota-Units-Remaining-*`,
  `X-Match-Rows-Remaining-Day`, `Retry-After`).
- Expanded the exception hierarchy: authentication (401), authorization (403),
  not found (404), validation (400/422), rate limit (429), concurrency limit,
  server (5xx), and transport errors. Existing exception classes are kept as
  parents, so `except` clauses written against 0.1.0 keep working.
- Added bounded retries for GET requests on network errors and 502/503/504,
  disabled by default (`max_retries=0`) because retried requests may consume
  extra server-side quota units; retry after 429 is additionally opt-in via
  `retry_on_rate_limit=True`.
- Enforced HTTPS base URLs (HTTP allowed only for localhost or with
  `allow_insecure_base_url=True`).
- Added a `User-Agent: foresportia-python/<version>` header and a `repr` that
  never exposes the API key.
- Kept all 0.1.0 dict-based methods unchanged (`me`, `usage`, `picks_today`,
  `matches_today`, `leagues`, `league_matches`, `world_cup_2026_matches`).
- Added an optional `ml` extra and `examples/ml_starter_features.py`.
- Rewrote the README around the current Starter plan surface.

## 0.1.0 - 2026-05-21

- Initial PyPI-ready private beta release.
- Added the initial synchronous `ForesportiaClient`.
- Added API key authentication through the `X-API-Key` header.
- Added `ForesportiaClient.from_env()` using the `FORES_API_KEY` environment
  variable.
- Added methods for account details, usage, today's picks, today's matches,
  available leagues, league matches, and World Cup 2026 matches.
- Added typed SDK exceptions for configuration, authentication, rate limiting,
  and API errors.
- Added initial public beta documentation and runnable examples.
