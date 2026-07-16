# Authentication

Foresportia API authentication uses an API key. The Python SDK expects the key
in the `FORES_API_KEY` environment variable when you use
`ForesportiaClient.from_env()`.

## Environment Variable

macOS and Linux:

```bash
export FORES_API_KEY="fs_developer_your_key_here"
```

PowerShell:

```powershell
$env:FORES_API_KEY = "fs_developer_your_key_here"
```

Do not include a real key in source code, examples, documentation, screenshots,
or issue reports.

## Header

The SDK sends the key with the `X-API-Key` request header:

```text
X-API-Key: fs_developer_your_key_here
```

The SDK never adds the key to request URLs, and the key never appears in
`repr(client)`, logs, or exception messages.

## HTTPS Only

The base URL must use HTTPS. Plain HTTP is only accepted for `localhost`, or
with `allow_insecure_base_url=True` for development/testing. Any other HTTP
base URL raises `ForesportiaConfigurationError`.

## Using `from_env()`

```python
from foresportia import ForesportiaClient

with ForesportiaClient.from_env() as client:
    leagues = client.list_leagues()

print(len(leagues.data))
```

If `FORES_API_KEY` is not set, the SDK raises
`ForesportiaConfigurationError`.

## Passing a Key Directly

Direct construction is available when your application already has a secure
configuration layer:

```python
from foresportia import ForesportiaClient

with ForesportiaClient(api_key="fs_developer_your_key_here", timeout=10.0) as client:
    data = client.usage()
```

Prefer environment variables, secret managers, or your hosting platform's secret
configuration instead of hard-coding keys.

## Errors

- `ForesportiaConfigurationError`: missing or empty local configuration,
  or an insecure base URL.
- `ForesportiaAuthenticationError` (401): missing, invalid, or revoked key.
- `ForesportiaAuthorizationError` (403): valid key but forbidden access
  (for example an endpoint or competition not enabled for your plan).
- `ForesportiaRateLimitError` (429): a rate or quota limit was exceeded;
  `ForesportiaConcurrencyLimitError` for the concurrency variant.
- `ForesportiaAPIError`: base class for all API-side errors.

All exceptions expose `status_code`, `error_code`, `endpoint`, `retry_after`,
and a `quota` snapshot when available. The API key is never included.

Developer keys are the recommended free starting point. Starter and existing
legacy beta keys use the same header and client. The SDK intentionally accepts
any non-empty key string and does not infer entitlements from `fs_developer_`,
`fs_starter_`, or `fs_beta_` prefixes; the server is the authority.

## Dashboard

The API dashboard can be used to monitor usage, view active key prefixes, and
generate a new key if needed:

- [English API dashboard](https://www.foresportia.com/en/api-dashboard.html)
- [French API dashboard](https://www.foresportia.com/api-dashboard.html)
