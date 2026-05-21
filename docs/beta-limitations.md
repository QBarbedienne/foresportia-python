# Beta Limitations

The Foresportia Python SDK and API are currently in private beta. This document
summarizes the practical limitations developers should account for while
building with the SDK.

## Access

- API access is limited to selected beta users.
- API keys are issued manually during the beta.
- Some endpoints, leagues, or data windows may be unavailable for a given key.

## Distribution

- The SDK is distributed as the `foresportia` package on PyPI.
- Pin the SDK version when using it in repeatable environments.

## API Stability

- Response schemas may change before a stable release.
- Fields may be added, renamed, removed, or made optional.
- New endpoints may be introduced during beta.
- Existing endpoints may change behavior as the API matures.

Use `.get()` when reading match fields and avoid treating beta response shapes
as a permanent contract.

## SDK Scope

- The SDK currently provides a synchronous client only.
- Responses are returned as dictionaries rather than typed model classes.
- The SDK is intentionally lightweight and does not include caching, retries,
  pagination helpers, or async support yet.

## Data Scope

- League and match coverage may vary.
- Refresh timing may vary during beta.
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
