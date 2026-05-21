# Foresportia Python SDK

Python SDK for the Foresportia API: football prediction data, model probabilities,
confidence badges, likely scores, and match analytics.

> **Beta warning**
>
> This SDK and the Foresportia API are currently in private beta. Endpoints and
> response schemas may evolve before a stable release. API access is currently
> available only to selected beta users.

## Installation

The package is not published on PyPI yet. Install it from GitHub for now:

```bash
pip install git+https://github.com/QBarbedienne/foresportia-python.git
```

PyPI distribution will come later.

## Get Beta Access

The Foresportia API is currently in private beta. To request access, see the
developer documentation:

- English docs: https://www.foresportia.com/en/developers.html
- French docs: https://www.foresportia.com/developpeurs.html

## API Key

Foresportia API access is currently granted manually during the private beta.
The initial API key is provided after beta access is approved.

Once your access is enabled, you can use the API dashboard to monitor usage,
view active key prefixes, and generate a new key if needed:

- English dashboard: https://www.foresportia.com/en/api-dashboard.html
- French dashboard: https://www.foresportia.com/api-dashboard.html

Expose your key as an environment variable:

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

## Check Account

```python
from foresportia import ForesportiaClient

client = ForesportiaClient.from_env()
account = client.me()

print(account["client"]["email"])
print(account["plan"])
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

## Current Beta Limitations

- The API is currently available to selected beta users.
- Endpoints and response schemas may evolve before a stable release.
- The SDK currently provides a synchronous client only.
- The SDK returns API responses as dictionaries.
- Bookmaker odds are not included.

## Language

This README is written in English for the Python developer ecosystem. French
documentation is also available:

https://www.foresportia.com/developpeurs.html

## Links

- Homepage: https://www.foresportia.com
- Developer docs (EN): https://www.foresportia.com/en/developers.html
- Developer docs (FR): https://www.foresportia.com/developpeurs.html
- API dashboard (EN): https://www.foresportia.com/en/api-dashboard.html
- API dashboard (FR): https://www.foresportia.com/api-dashboard.html

## Disclaimer

Foresportia provides model probabilities and football analytics data. It does
not provide bookmaker odds and is not betting advice.

## License

MIT.
