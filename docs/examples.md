# Examples

The repository includes runnable examples in the `examples/` directory.

Before running an example, install the SDK and set your API key:

```bash
pip install foresportia
export FORES_API_KEY="fs_beta_your_key_here"
```

On PowerShell:

```powershell
$env:FORES_API_KEY = "fs_beta_your_key_here"
```

## Machine Learning Feature Extraction

```bash
pip install "foresportia[ml]"
python examples/ml_starter_features.py
```

Fetches upcoming matches for a competition, extracts probabilities, markets,
and confidence into a feature matrix, and optionally fits a small
scikit-learn model. Foresportia outputs are model probabilities, not
guaranteed predictions; you need your own historical labels to train anything
meaningful.

## Print Today's Picks

```bash
python examples/print_today_picks.py
```

Prints a compact list of today's matches, predicted picks, confidence
indicators when present, and likely scores when present.

## Export Today's Picks to CSV

```bash
python examples/export_today_picks_to_csv.py
```

Writes `today_picks.csv` in the current working directory with common match and
prediction fields. Missing fields are written as blank values.

## Filter High Confidence Matches

```bash
python examples/filter_high_confidence_matches.py
```

Prints matches whose confidence value passes the example threshold. This is
only a filtering example and should not be interpreted as betting advice.

## Other Examples

The repository also includes `examples/todays_picks.py`,
`examples/league_matches.py`, and `examples/world_cup_2026.py`, which show
direct use of the SDK methods.

## Error Handling Pattern

```python
from foresportia import (
    ForesportiaAPIError,
    ForesportiaAuthenticationError,
    ForesportiaAuthorizationError,
    ForesportiaClient,
    ForesportiaConfigurationError,
    ForesportiaNotFoundError,
    ForesportiaRateLimitError,
)

try:
    with ForesportiaClient.from_env() as client:
        picks = client.list_today_picks()
except ForesportiaConfigurationError as exc:
    print(f"Configuration error: {exc}")
except ForesportiaAuthenticationError as exc:
    print(f"Invalid API key: {exc}")
except ForesportiaAuthorizationError as exc:
    print(f"Access forbidden: {exc.error_code}")
except ForesportiaNotFoundError as exc:
    print(f"Not found: {exc.endpoint}")
except ForesportiaRateLimitError as exc:
    print(f"Rate limited, retry after {exc.retry_after} seconds")
except ForesportiaAPIError as exc:
    print(f"API error on {exc.endpoint}: {exc.status_code} {exc.error_code}")
```

## Conditional Requests with ETags

```python
first = client.get_match(match_id)
second = client.get_match(match_id, etag=first.etag)
detail = first.data if second.not_modified else second.data
```
