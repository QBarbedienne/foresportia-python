# Changelog

All notable changes to the Foresportia Python SDK will be documented in this
file.

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
