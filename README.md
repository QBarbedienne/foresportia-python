# Foresportia Python SDK

Python SDK for the Foresportia API: football prediction data, model probabilities,
confidence badges, likely scores, and match analytics.

> **Beta warning**
>
> This SDK and the Foresportia API are currently in private beta. Endpoints and
> response schemas may evolve before a stable release.

## Installation

The package is not published on PyPI yet. Install it from GitHub for now:

```bash
pip install git+https://github.com/QBarbedienne/foresportia-python.git
```

PyPI distribution will come later.

## API Key

Create an API key from the Foresportia API dashboard, then expose it as an
environment variable:

```bash
export FORES_API_KEY="fs_beta_your_key_here"
```

The SDK sends the key only in the `X-API-Key` header. It never adds the key to a
URL.

## Quick Start

```python
from foresportia import ForesportiaClient

client = ForesportiaClient.from_env()

print(client.me())
print(client.picks_today())
```

## World Cup 2026 Example

```python
from foresportia import ForesportiaClient

client = ForesportiaClient.from_env()

matches = client.world_cup_2026_matches(limit=10)
for match in matches.get("matches", []):
    print(match["home_team"], match["away_team"], match.get("pick"))
```

## League Matches Example

```python
from foresportia import ForesportiaClient

client = ForesportiaClient.from_env()

matches = client.league_matches("CHN", include="all", days=14, limit=10)
for match in matches.get("matches", []):
    print(match["home_team"], match["away_team"], match.get("pick"))
```

## Error Handling

```python
from foresportia import (
    ForesportiaAPIError,
    ForesportiaAuthError,
    ForesportiaClient,
    ForesportiaConfigurationError,
    ForesportiaRateLimitError,
)

try:
    client = ForesportiaClient.from_env()
    data = client.picks_today()
except ForesportiaConfigurationError as exc:
    print(f"Configuration error: {exc}")
except ForesportiaAuthError as exc:
    print(f"Authentication error: {exc}")
except ForesportiaRateLimitError as exc:
    print(f"Rate limit exceeded: {exc}")
except ForesportiaAPIError as exc:
    print(f"API error on {exc.endpoint}: {exc.status_code}")
```

## Available Methods

```python
client.me()
client.usage()
client.picks_today()
client.matches_today()
client.leagues()
client.league_matches("CHN", include="all", days=14, limit=10)
client.world_cup_2026_matches(limit=10)
```

## Links

- Homepage: https://www.foresportia.com
- Developer docs: https://www.foresportia.com/en/developers.html
- API dashboard: https://www.foresportia.com/en/api-dashboard.html

## Disclaimer

Foresportia provides model probabilities and football analytics data. It does
not provide bookmaker odds and is not betting advice.

## License

MIT.
