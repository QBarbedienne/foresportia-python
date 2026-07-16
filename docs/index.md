# Foresportia Python SDK

Official Python SDK for the [Foresportia API](https://www.foresportia.com/api/docs/),
a football analytics API that provides match data, model probabilities,
predicted picks, confidence signals, and Core Analytics payloads for building
or enriching football prediction models.

Foresportia returns probabilistic forecasts and analytics. It does not provide
betting advice, bookmaker odds, or guaranteed outcomes, and it is not a live
score feed.

## Official links

- [Foresportia API documentation](https://www.foresportia.com/api/docs/)
- [LLM-friendly API reference](https://www.foresportia.com/api/docs/llms-full.txt)
- [Foresportia website](https://www.foresportia.com/en) ([FR](https://www.foresportia.com/), [ES](https://www.foresportia.com/es))
- [API dashboard](https://www.foresportia.com/en/api-dashboard.html)
- [PyPI package](https://pypi.org/project/foresportia/)
- [GitHub repository](https://github.com/QBarbedienne/foresportia-python)

## Quick install

```bash
pip install foresportia
```

## Quick start

```python
from foresportia import ForesportiaClient

with ForesportiaClient.from_env() as client:
    leagues = client.list_leagues()
    for league in leagues.data:
        print(league.code, league.name, league.matches_available)

    picks = client.list_today_picks()
    for match in picks.data:
        print(match.home_team, "vs", match.away_team, match.pick)
```

Typed methods return an `ApiResponse` with `data` (typed result), `payload`
(full JSON dict), `etag`, `quota`, and `status_code`. The dict-based methods
from 0.1.0 (`me()`, `picks_today()`, `leagues()`, ...) keep working unchanged.

## Documentation

- [Getting Started](getting-started.md) — install, configure your key, and make
  a first request.
- [Authentication](authentication.md) — how API keys are handled.
- [Examples](examples.md) — runnable scripts, including a machine learning
  feature-extraction example.
- [Response Fields](response-fields.md) — typed models and payload shapes.
- [Plans and Limitations](plan-limitations.md) — Developer, Starter, and
  legacy-access constraints.
