# Beta Limitations

This document summarizes the practical limitations developers should account
for while building with the SDK.

## Access

- API keys are issued through Foresportia plans; some endpoints, competitions,
  or data windows may be unavailable for a given key.
- `POST /v1/matches/bulk` is available on the Starter plan.

## Distribution

- The SDK is distributed as the `foresportia` package on PyPI.
- Pin the SDK version when using it in repeatable environments.

## API Stability

- Response schemas may still evolve. New optional fields may be added without
  a major SDK version change.
- The SDK's typed models are tolerant: added fields never break parsing and
  remain accessible through `.raw`.

## SDK Scope

- The SDK provides a synchronous client only (no async client yet).
- Retries are **disabled by default** (`max_retries=0`): a request that times
  out client-side may still have been counted against your quota server-side,
  so each retry can consume an extra quota unit. Enable retries explicitly
  with `max_retries=...` and, for 429, `retry_on_rate_limit=True`.
- ETag conditional requests are supported (`etag=` parameter, `not_modified`),
  but the SDK does not include a disk cache.
- The SDK parses quota headers but does not reproduce server-side quota rules
  and cannot prevent overruns.

## Data Scope

- Competition and match coverage vary by plan and key configuration.
- Refresh timing may vary.
- Likely scores, confidence indicators, and probabilities may be missing for
  some matches.
- Bookmaker odds are not included.

## Model Output

Foresportia model outputs are probabilities and analytics, not guarantees. Do
not present them as certain outcomes or betting instructions. Any downstream
product should communicate uncertainty clearly.

## Betting Disclaimer

Foresportia provides probabilities and football analytics only. It does not
provide betting advice, financial advice, bookmaker odds, guaranteed outcomes,
or instructions to place wagers.
