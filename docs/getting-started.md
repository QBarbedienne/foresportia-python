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
export FORES_API_KEY="fs_developer_your_key_here"
```

On PowerShell:

```powershell
$env:FORES_API_KEY = "fs_developer_your_key_here"
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

Developer includes up to 7 days of verified history; Starter includes up to
90. The server applies the effective entitlement and may return
`history_window_exceeded`. `response.history_available_from` reports the
currently populated lower bound, which can be more recent while the archive
fills.

Continue a paginated result with the opaque cursor:

```python
page = client.list_league_matches("CHN", include="past", days=7, limit=50)
while page.next_cursor:
    page = client.list_league_matches(
        "CHN", include="past", days=7, limit=50, cursor=page.next_cursor
    )
```

Or stream matches lazily with
`client.iter_league_matches("CHN", include="past", days=7, limit=50)`.

For history specifically, `list_league_history()` and `iter_league_history()`
are thin wrappers that always send `include="past"`; they take the same
parameters and return the same types, metadata, and errors as the methods
above. On a returned row, `match.is_final` mirrors `status == "final"` and
`match.predicted_outcome` exposes the published pre-match pick (`"home"`,
`"draw"`, `"away"`, or `None`), while `match.result_score` holds the final
score from the API.

By default `days` is omitted, so the server chooses the window from the key's
history entitlement, capped at 31 days per request. Pass `days` for an explicit
window:

```python
with ForesportiaClient.from_env() as client:
    # Automatically uses the available window, capped at 31 days per request.
    history = client.list_league_history("SUE")

    # The user can also pick a shorter, explicit window.
    history = client.list_league_history("SUE", days=3)

    for match in client.iter_league_history("SUE"):
        if match.is_final:
            print(match.home_team, match.away_team,
                  match.result_score, match.predicted_outcome)
```

Developer currently gets 7 days of history and Starter a 90-day rolling
entitlement, but an automatic request stays capped at 31 days.
`iter_league_history()` paginates the requested window and does not split a
90-day entitlement into several windows. A window may legitimately be empty, and
the server stays the source of truth.

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
- Read [plan-limitations.md](plan-limitations.md) for Developer, Starter, and
  legacy-access constraints.
