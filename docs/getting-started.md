# Getting Started

This guide shows how to install the private beta Foresportia Python SDK,
authenticate with an API key, and make your first request.

## Prerequisites

- Python 3.10 or newer.
- Private beta access to the Foresportia API.
- A Foresportia API key.

The SDK is currently intended for selected beta users. API behavior, response
fields, and limits may change before a stable release.

## Installation

Install the package from PyPI:

```bash
pip install foresportia
```

For local development from a cloned checkout:

```bash
pip install -e ".[dev]"
```

## Configure Your API Key

Set your API key in the `FORES_API_KEY` environment variable:

```bash
export FORES_API_KEY="fs_beta_your_key_here"
```

On PowerShell:

```powershell
$env:FORES_API_KEY = "fs_beta_your_key_here"
```

The SDK reads this variable with `ForesportiaClient.from_env()` and sends it to
the API through the `X-API-Key` header.

## First Request

```python
from foresportia import ForesportiaClient

with ForesportiaClient.from_env() as client:
    account = client.me()
    picks = client.picks_today()

print(account.get("plan"))
print(f"Matches returned: {len(picks.get('matches', []))}")
```

## Fetch League Matches

```python
from foresportia import ForesportiaClient

with ForesportiaClient.from_env() as client:
    data = client.league_matches("CHN", include="all", days=14, limit=10)

for match in data.get("matches", []):
    print(match.get("home_team"), "vs", match.get("away_team"))
```

## Next Steps

- Review [authentication.md](authentication.md) before deploying the SDK.
- Review [response-fields.md](response-fields.md) before depending on specific
  fields.
- Try the scripts in [examples.md](examples.md).
- Read [beta-limitations.md](beta-limitations.md) for current beta constraints.
