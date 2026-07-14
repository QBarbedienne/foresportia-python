# Getting Started

This guide shows how to install the Foresportia Python SDK, authenticate with
an API key, and make your first requests.

## Prerequisites

- Python 3.9 or newer.
- Access to the Foresportia API and an API key.

## Installation

Install the package from PyPI:

```bash
pip install foresportia
```

Optional extras:

```bash
pip install "foresportia[ml]"    # numpy + scikit-learn for the ML example
pip install -e ".[dev]"          # local development from a cloned checkout
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
the API through the `X-API-Key` header only — never in URLs.

## First Request

```python
from foresportia import ForesportiaClient

with ForesportiaClient.from_env() as client:
    leagues = client.list_leagues()

for league in leagues.data:
    print(league.code, league.name, league.activity_status)
```

## Fetch League Matches

```python
from foresportia import ForesportiaClient

with ForesportiaClient.from_env() as client:
    response = client.list_league_matches(
        "PREMIER_LEAGUE",
        include="upcoming",
        days=14,
        limit=50,
    )

for match in response.data:
    print(match.kickoff, match.home_team, "vs", match.away_team, match.pick)
```

`include` accepts `"upcoming"`, `"past"`, or `"all"`; `days` goes up to 31 and
`limit` up to 500. `start` accepts a `YYYY-MM-DD` string or a `datetime.date`.

## Match Detail and Bulk

Match IDs from list endpoints look like `fsm:v1:<64 hex characters>`. Pass them
exactly as returned:

```python
match = client.get_match(match_id)
print(match.data.probabilities)

bulk = client.get_matches_bulk([id_1, id_2])
for detail in bulk.data.results:
    print(detail.id, detail.home_team)
for error in bulk.data.errors:
    print("failed:", error.match_id, error.code)
```

## Next Steps

- Review [authentication.md](authentication.md) before deploying the SDK.
- Review [response-fields.md](response-fields.md) before depending on specific
  fields.
- Try the scripts in [examples.md](examples.md).
- Read [beta-limitations.md](beta-limitations.md) for current constraints.
