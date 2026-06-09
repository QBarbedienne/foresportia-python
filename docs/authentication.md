# Authentication

Foresportia API authentication uses an API key issued during the private beta.
The Python SDK expects the key in the `FORES_API_KEY` environment variable when
you use `ForesportiaClient.from_env()`.

## Environment Variable

macOS and Linux:

```bash
export FORES_API_KEY="fs_beta_your_key_here"
```

PowerShell:

```powershell
$env:FORES_API_KEY = "fs_beta_your_key_here"
```

Do not include a real key in source code, examples, documentation, screenshots,
or issue reports.

## Header

The SDK sends the key with the `X-API-Key` request header:

```text
X-API-Key: fs_beta_your_key_here
```

The SDK does not add the key to request URLs.

## Using `from_env()`

```python
from foresportia import ForesportiaClient

with ForesportiaClient.from_env() as client:
    account = client.me()

print(account.get("plan"))
```

If `FORES_API_KEY` is not set, the SDK raises
`ForesportiaConfigurationError`.

## Passing a Key Directly

Direct construction is available when your application already has a secure
configuration layer:

```python
from foresportia import ForesportiaClient

with ForesportiaClient(api_key="fs_beta_your_key_here") as client:
    data = client.usage()
```

Prefer environment variables, secret managers, or your hosting platform's secret
configuration instead of hard-coding keys.

## Errors

- `ForesportiaConfigurationError`: missing or empty local configuration.
- `ForesportiaAuthError`: invalid key, expired key, forbidden access, or an
  endpoint unavailable for the key.
- `ForesportiaRateLimitError`: the current key exceeded a rate or quota limit.
- `ForesportiaAPIError`: other API, network, or response parsing errors.

## Dashboard

After access is enabled, the API dashboard can be used to monitor usage, view
active key prefixes, and generate a new key if needed:

- [English API dashboard](https://www.foresportia.com/en/api-dashboard.html)
- [French API dashboard](https://www.foresportia.com/api-dashboard.html)
