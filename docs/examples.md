# Examples

The repository includes simple runnable examples in the `examples/` directory.
They are intentionally small and use `.get()` so they continue to work while the
private beta schema evolves.

Before running an example, install the SDK and set your API key:

```bash
pip install foresportia
export FORES_API_KEY="fs_beta_your_key_here"
```

On PowerShell:

```powershell
$env:FORES_API_KEY = "fs_beta_your_key_here"
```

## Print Today's Picks

```bash
python examples/print_today_picks.py
```

Prints a compact list of today's matches, predicted picks, confidence indicators
when present, and likely scores when present.

## Export Today's Picks to CSV

```bash
python examples/export_today_picks_to_csv.py
```

Writes `today_picks.csv` in the current working directory with common match and
prediction fields. Missing beta fields are written as blank values.

## Filter High Confidence Matches

```bash
python examples/filter_high_confidence_matches.py
```

Prints matches whose confidence or stability value appears to pass the example
threshold. This is only a filtering example and should not be interpreted as
betting advice.

## Existing Examples

The repository also includes:

- `examples/todays_picks.py`
- `examples/league_matches.py`
- `examples/world_cup_2026.py`

These show direct use of the current SDK methods.

## Error Handling Pattern

```python
from foresportia import (
    ForesportiaAPIError,
    ForesportiaAuthError,
    ForesportiaClient,
    ForesportiaConfigurationError,
    ForesportiaRateLimitError,
)

try:
    with ForesportiaClient.from_env() as client:
        data = client.picks_today()
except ForesportiaConfigurationError as exc:
    print(f"Configuration error: {exc}")
except ForesportiaAuthError as exc:
    print(f"Authentication or authorization error: {exc}")
except ForesportiaRateLimitError as exc:
    print(f"Rate limit exceeded: {exc}")
except ForesportiaAPIError as exc:
    print(f"API error on {exc.endpoint}: {exc.status_code}")
```
